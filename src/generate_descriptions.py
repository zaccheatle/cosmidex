"""
Planetary data script to connect to the Google Gemini API and generate
experiential planet descriptions.
"""

# import dependencies
import logging
import os
import sys
import time
import zlib

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from google import genai
from google.genai import types
from psycopg2.extensions import connection as PGConnection

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from cosmidex_api.database import connection_params

load_dotenv()

# initialize gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
TEXT_MODEL = "gemini-3.5-flash"

# safety cap on planets generated in a single run
MAX_PLANETS_PER_RUN = 200

SYSTEM_PROMPT = """
You are a science writer for CosmiDex, an exoplanet explorer app. Write a
vivid, second-person description (AT MOST 2 sentences) of standing on or near
the given exoplanet. Ground it in the actual data — temperature, gravity,
star light, atmosphere/composition — and pick one or two concrete, specific
details rather than listing everything.

Write like a knowledgeable person texting a friend a cool fact, not like ad
copy. Strictly avoid: opening with "Imagine...", "Picture...", "Whoa...", or
"Standing on...", exclamation points, and generic space-metaphor filler
("cosmic dance", "otherworldly wonder", "tropical paradise", "breathtaking",
"awe-inspiring"). Do not invent details that contradict the data (e.g. don't
describe breathable air on a gas giant). Output only the description, no
preamble.
"""

# Rotated per-planet so descriptions don't all default to the same opening
# pattern (each API call is stateless, so the model has no memory of what
# it wrote for other planets to vary against).
OPENING_STYLES = [
    "Open with a sensory detail (light, temperature, or texture) — not a scene-setting phrase.",
    "Open by comparing something on this planet directly to Earth.",
    "Open with what the sky or the host star looks like from the surface.",
    "Open with how your body would feel (weight, breathing, temperature) in the first few seconds.",
    "Open with the ground or terrain underfoot.",
]


def opening_style_for(planet_name: str) -> str:
    """Deterministically pick an opening style so the same planet always gets
    the same style on reruns, but different planets get variety."""
    return OPENING_STYLES[zlib.crc32(planet_name.encode()) % len(OPENING_STYLES)]

# set up logger
logging.basicConfig(level=logging.INFO)


def get_planets(conn: PGConnection) -> list[dict]:
    """Retrieve descriptive stats for potentially habitable planets (Tier 1/2/3)
    that don't have a description yet.

    Only planets missing a row in marts.planet_descriptions are returned, so
    re-running this after a rescrape only generates descriptions for newly-qualifying
    planets.

    Args:
        conn (PGConnection): Postgres db connection.

    Returns:
        List[Dict]: Planet dictionaries with the fields needed to build a description prompt.
    """

    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            """
            SELECT
                planet_name,
                host_star_name,
                habitability_tier,
                estimated_planet_climate,
                planet_composition,
                planet_size_class,
                gravity_description,
                star_spectral_type,
                star_temp_description,
                star_life_stage,
                orbital_distance_description,
                equilibrium_temp_celsius,
                esi_score
            FROM marts.mart_planet_profile AS pp
            WHERE pp.habitability_tier IN ('Tier 1', 'Tier 2', 'Tier 3')
                AND NOT EXISTS (
                    SELECT 1 FROM marts.planet_descriptions AS pd
                    WHERE pd.planet_name = pp.planet_name
                )
            ORDER BY esi_score DESC NULLS LAST
            LIMIT %s
        """,
            (MAX_PLANETS_PER_RUN,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return list(rows)

    except psycopg2.DatabaseError as e:
        logging.error(f"Query failed: {e}")
        return []


def build_prompt(planet: dict) -> str:
    """Build the user prompt describing a planet's stats for Gemini.

    Args:
        planet (dict): Planet stats returned by get_planets().

    Returns:
        str: The prompt to send to Gemini.
    """

    esi_text = (
        f"{planet['esi_score']:.3f}" if planet["esi_score"] is not None else "unknown"
    )

    return (
        f"Planet: {planet['planet_name']}, orbiting {planet['host_star_name']}.\n"
        f"Composition: {planet['planet_composition']}\n"
        f"Size class: {planet['planet_size_class']}\n"
        f"Gravity: {planet['gravity_description']}\n"
        f"Climate: {planet['estimated_planet_climate']}\n"
        f"Equilibrium temperature: {planet['equilibrium_temp_celsius']}°C\n"
        f"Orbital distance: {planet['orbital_distance_description']}\n"
        f"Host star: {planet['star_spectral_type']}, {planet['star_temp_description']}, {planet['star_life_stage']}\n"
        f"Habitability classification: {planet['habitability_tier']}\n"
        f"Earth Similarity Index: {esi_text}\n"
        f"Opening instruction: {opening_style_for(planet['planet_name'])}"
    )


def generate_description(prompt: str) -> str | None:
    """Generate an experiential planet description using Gemini.

    Args:
        prompt (str): Prompt describing the planet's stats.

    Returns:
        str | None: Generated description text or None on failure.
    """
    try:
        response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=200,
                temperature=0.8,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        return response.text
    except Exception as e:
        logging.error(f"Description generation error: {e}")
        return None


def save_description(
    conn: PGConnection,
    planet_name: str,
    description: str,
    generation_model: str,
) -> None:
    """Store a planet's description in the db.

    Args:
        conn (PGConnection): Postgres db connection.
        planet_name (str): Planet's name.
        description (str): Generated description text.
        generation_model (str): Model used to generate the description.

    Returns:
        None.

    Raises:
        DatabaseError: Error running db query.
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO marts.planet_descriptions
                (planet_name, description, generation_model)
            VALUES
                (%s, %s, %s)
            ON CONFLICT (planet_name)
            DO UPDATE SET
                description = EXCLUDED.description,
                generated_at = now(),
                generation_model = EXCLUDED.generation_model
        """,
            (planet_name, description, generation_model),
        )

        conn.commit()
        cursor.close()
    except psycopg2.DatabaseError as e:
        logging.error(f"Query error: {e}")


def main():
    """Runs planet description generation flow."""
    conn = psycopg2.connect(**connection_params)
    planets = get_planets(conn)

    saved_count = 0
    failed_count = 0
    failed_planet_list = []
    total_planet_count = len(planets)

    for planet in planets:
        planet_name = planet["planet_name"]
        prompt = build_prompt(planet)
        description = generate_description(prompt)
        time.sleep(1)

        if description is not None:
            save_description(conn, planet_name, description, TEXT_MODEL)
            saved_count += 1
            logging.info(f"Description saved for {planet_name}.")
        else:
            failed_count += 1
            failed_planet_list.append(planet_name)
            logging.warning(f"Description generation failed for {planet_name}")

    conn.close()
    return {
        "total_planets": total_planet_count,
        "saved": saved_count,
        "failed": failed_count,
        "failed_planets": failed_planet_list,
    }


if __name__ == "__main__":
    result = main()
    logging.info(f"Pipeline complete: {result}")
