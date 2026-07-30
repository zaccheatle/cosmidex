"""
Planetary data script to connect to the OpenAI API and generate experiential
planet descriptions with GPT-4o.
"""

# import dependencies
import logging
import os
import sys
import time

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from openai import OpenAI
from psycopg2.extensions import connection as PGConnection

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from cosmidex_api.database import connection_params

load_dotenv()

# initialize openai client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# top N planets (by ESI) to generate descriptions for
TOP_N_PLANETS = 25

SYSTEM_PROMPT = """
You are a science communicator for CosmiDex, an exoplanet explorer app, writing
in the informal, vivid, enthusiastic voice of someone like Neil deGrasse Tyson
explaining a cool space fact to a casual space enthusiast — approachable and
fun, not dry or textbook-y, but still scientifically grounded. Write a
second-person description of what it might feel like to stand on or near the
given exoplanet, in AT MOST 2 short sentences — punchy, not exhaustive. Pick
only the one or two most striking sensory details (temperature, gravity, star
light, atmosphere/composition) rather than covering everything. Do not invent
details that contradict the data (e.g. don't describe breathable air on a gas
giant). Write only the description, no preamble or planet name repetition.
"""

# set up logger
logging.basicConfig(level=logging.INFO)


def get_planets(conn: PGConnection) -> list[dict]:
    """Retrieve descriptive stats for the top N planets by ESI score.

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
            FROM marts.mart_planet_profile
            ORDER BY esi_score DESC NULLS LAST
            LIMIT %s
        """,
            (TOP_N_PLANETS,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return list(rows)

    except psycopg2.DatabaseError as e:
        logging.error(f"Query failed: {e}")
        return []


def build_prompt(planet: dict) -> str:
    """Build the user prompt describing a planet's stats for GPT-4o.

    Args:
        planet (dict): Planet stats returned by get_planets().

    Returns:
        str: The prompt to send to GPT-4o.
    """

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
        f"Earth Similarity Index: {planet['esi_score']:.3f}"
    )


def generate_description(prompt: str) -> str | None:
    """Generate an experiential planet description using GPT-4o.

    Args:
        prompt (str): Prompt describing the planet's stats.

    Returns:
        str | None: Generated description text or None on failure.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.8,
        )
        return response.choices[0].message.content
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
            save_description(conn, planet_name, description, "gpt-4o")
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
