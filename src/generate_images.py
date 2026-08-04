"""Planetary data script to connect to the Google Gemini API to generate planet images."""

import logging
import os
import sys
import time

import boto3
import psycopg2
import psycopg2.extras
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from google import genai
from google.genai import types
from psycopg2.extensions import connection as PGConnection

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from cosmidex_api.database import connection_params

load_dotenv()

s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION"))

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
IMAGE_MODEL = "gemini-3.1-flash-image"

# 4:3 matches the app's comparison-image panel much more closely than the
# model's 16:9 default, which left large empty letterbox bands above/below
# the image in that panel.
IMAGE_CONFIG = types.GenerateContentConfig(
    image_config=types.ImageConfig(aspect_ratio="4:3"),
)

# safety cap on planets generated in a single run
MAX_PLANETS_PER_RUN = 200


logging.basicConfig(level=logging.INFO)


def get_planets(conn: PGConnection) -> list[dict]:
    """Retrieve planet name and image prompt body for potentially habitable
    planets (Tier 1/2/3) that don't have images yet.

    Planet image prompt bodies are stored in the marts.mart_planet_image_prompt
    materialized view; habitability_tier and ESI score live on
    marts.mart_planet_profile, so the two are joined here. Only planets missing a
    row in marts.planet_images are returned, so re-running this after a rescrape
    only generates images for newly-qualifying planets.

    Args:
        conn (PGConnection): Postgres db connection.

    Returns:
        list[dict]: Planet dictionaries in the format list[{planet_name, image_prompt_body}].

    Raises:
        DatabaseError: Error running query against postgres.
    """

    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            """
            SELECT
                ip.planet_name,
                ip.image_prompt_body
            FROM marts.mart_planet_image_prompt AS ip
            JOIN marts.mart_planet_profile AS pp ON ip.planet_name = pp.planet_name
            WHERE pp.habitability_tier IN ('Tier 1', 'Tier 2', 'Tier 3')
                AND NOT EXISTS (
                    SELECT 1 FROM marts.planet_images AS pi
                    WHERE pi.planet_name = ip.planet_name
                )
            ORDER BY pp.esi_score DESC NULLS LAST
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


def generate_images(prompt: str) -> bytes | None:
    """Generate a planet image using Google's Gemini image model.

    Args:
        prompt (str): Image prompt describing a planet's characteristics.

    Returns:
        bytes | None: Raw image bytes or None on failure.
    """
    try:
        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=prompt,
            config=IMAGE_CONFIG,
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                return part.inline_data.data

        logging.error("Gemini response contained no image data")
        return None
    except Exception as e:
        logging.error(f"Image generation error: {e}")
        return None


def upload_to_s3(image_bytes: bytes, planet_name: str) -> str | None:
    """Upload the planet AI image to s3.

    Args:
        image_bytes (bytes): Raw bytes of downloaded planet image .png file.
        planet_name (str): Planet's name.

    Returns:
        str | None: URL where the image is stored in S3, or None on failure.

    Raises:
        ClientError: Error connecting to or uploading objects to S3.
    """

    filename = f"{planet_name.replace(' ', '_')}.png"
    prefix = "exoplanet-images"
    bucket = os.getenv("AWS_S3_BUCKET")
    region = os.getenv("AWS_REGION")
    key = f"{prefix}/{filename}"
    url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"

    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=image_bytes,
            ContentType="image/png",
            CacheControl="no-cache, max-age=0, must-revalidate",
        )
        return url
    except ClientError as e:
        logging.error(f"Error with s3 upload: {e}")
        return None


def save_image(
    conn: PGConnection,
    planet_name: str,
    image_url: str,
    prompt: str,
    generation_model: str,
) -> None:
    """Store S3 url of the planet's comparison image to db.

    Args:
        conn (PGConnection): Postgres db connection.
        planet_name (str): Planet's name.
        image_url (str): S3 url of the Earth-comparison image.
        prompt (str): Image prompt body describing the planet's characteristics.
        generation_model (str): Model used to generate the image.

    Returns:
        None.

    Raises:
        DatabaseError: Error running db query.
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO marts.planet_images
                (planet_name, image_url, image_prompt, generation_model)
            VALUES
                (%s, %s, %s, %s)
            ON CONFLICT (planet_name)
            DO UPDATE SET
                image_url = EXCLUDED.image_url,
                image_prompt = EXCLUDED.image_prompt,
                generated_at = now(),
                generation_model = EXCLUDED.generation_model
        """,
            (planet_name, image_url, prompt, generation_model),
        )

        conn.commit()
        cursor.close()
    except psycopg2.DatabaseError as e:
        logging.error(f"Query error: {e}")


def main():
    """Runs planet AI image processing flow — generates one Earth-comparison
    image per planet."""
    conn = psycopg2.connect(**connection_params)
    planets = get_planets(conn)

    saved_count = 0
    failed_count = 0
    failed_planet_list = []
    total_planet_count = len(planets)

    for planet_dict in planets:
        planet_name = planet_dict["planet_name"]
        body = planet_dict["image_prompt_body"]

        image_bytes = generate_images(body)
        time.sleep(3)

        if image_bytes is None:
            failed_count += 1
            failed_planet_list.append(planet_name)
            logging.warning(f"Image generation failed for {planet_name}")
            continue

        image_url = upload_to_s3(image_bytes, planet_name)

        if image_url is None:
            failed_count += 1
            failed_planet_list.append(planet_name)
            logging.warning(f"S3 upload failed for {planet_name}")
            continue

        save_image(conn, planet_name, image_url, body, IMAGE_MODEL)
        saved_count += 1
        logging.info(f"Image saved for {planet_name}.")

    conn.close()
    return {
        "total_planets": total_planet_count,
        "saved": saved_count,
        "failed": failed_count,
        "success_rate": f"{(saved_count / total_planet_count * 100):.1f}%"
        if total_planet_count > 0
        else "N/A",
        "failed_planets": failed_planet_list,
    }


if __name__ == "__main__":
    result = main()
    logging.info(f"Pipeline complete: {result}")
