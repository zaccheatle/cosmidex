"""
Planetary data script to connect to openai api to generate planet images
"""

# import dependencies
import logging
import os
import sys
import time

import boto3
import psycopg2
import psycopg2.extras
import requests
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from openai import OpenAI
from psycopg2.extensions import connection as PGConnection

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from planetary_api.database import connection_params

load_dotenv()

# initialize s3 client
s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION"))

# initialize openai client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# set up logger
logging.basicConfig(level=logging.INFO)


# retrieve notable planets and their image prompt from db
def get_planets(conn: PGConnection) -> list[dict]:
    """Retrieve planet name and image prompt from postgres.

    Planet image prompts are stored in the marts.mart_planet_image_prompt materialized view.
    We need the images to pass to the openai client to generate images using dall-e-3.

    Args:
        conn: (PGConnection): Postgres db connection.

    Returns:
        List[Dict]: Returns a list of planet dictionaries in the format list[{planet_name, image_prompt}].

    Raises:
        DatabaseError: Error running query against postgres.
    """

    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT
                planet_name, image_prompt
            FROM marts.mart_planet_image_prompt
            WHERE is_notable = true
        """)
        rows = cursor.fetchall()
        cursor.close()
        return list(rows)

    except psycopg2.DatabaseError as e:
        logging.error(f"Query failed: {e}")
        return []


# initialize openai client
def generate_images(prompt: str) -> tuple | None:
    """Generate planet image using AI prompt.

    Pass an image prompt to generate an AI image url.

    Args:
        prompt (str): Image prompt describing a planets characteristics.

    Returns:
        tuple (image_url, image_bytes): Returns the generated image url and image bytes.

    Raises:
        Exception: Error generating the image_url.
    """
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url  # type: ignore
        image = requests.get(image_url)  # type: ignore
        image_bytes = image.content
        return image_url, image_bytes
    except Exception as e:
        logging.error(f"Image generation error: {e}")
        return None


def upload_to_s3(image_bytes: bytes, planet_name: str) -> str | None:
    """Upload the planet AI image to s3.

    Args:
        image_bytes (bytes): Raw bytes of downloaded planet image .png file.
        planet_name (str): Planet's name.

    Returns:
        url where image is stored in s3.

    Raises:
        ClientError: Error connecting to or uploading objects to S3.
    """

    filename = f"{planet_name.replace(' ', '_')}.png"
    bucket = os.getenv("AWS_S3_BUCKET")
    region = os.getenv("AWS_REGION")
    url = f"https://{bucket}.s3.{region}.amazonaws.com/{filename}"

    try:
        s3_client.put_object(
            Bucket=os.getenv("AWS_S3_BUCKET"),
            Key=filename,
            Body=image_bytes,
            ContentType="image/png",
        )
        return url
    except ClientError as e:
        logging.error(f"Error with s3 upload: {e}")
        return None


# save image to postgres
def save_image(
    conn: PGConnection,
    planet_name: str,
    image_url: str,
    prompt: str,
    generation_model: str,
) -> None:
    """Save temporary AI image url to postgres.

    AI image urls provided by the OpenAI API will only last 1 hr.
    Will save these temp urls to postgres as backup.

    Args:
        conn (PGConnection): Postgres db connection.
        planet_name (str): Planet's name.
        image_url (str): Temp url to generated image provided by the model.
        prompt (str): Image prompt describing the planets characteristics
        generation_model (str): Model used to generate the image url and .png file.

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
    """Runs planet AI image processing flow."""
    conn = psycopg2.connect(**connection_params)
    planets = get_planets(conn)

    saved_to_s3_count = 0
    failed_to_s3_count = 0
    saved_to_db_count = 0
    failed_to_db_count = 0
    failed_planet_list = []
    total_planet_count = len(planets)

    for planet_dict in planets:
        planet_name = planet_dict["planet_name"]
        prompt = planet_dict["image_prompt"]
        result = generate_images(prompt)
        time.sleep(1)
        if result is not None:
            temp_url, image_bytes = result
            permanent_url = upload_to_s3(image_bytes, planet_name)
            logging.info("Image successfully uploaded to s3!")
            saved_to_s3_count += 1
            if permanent_url is not None:
                save_image(
                    conn=conn,
                    planet_name=planet_name,
                    image_url=permanent_url,
                    prompt=prompt,
                    generation_model="dall-e-3",
                )
                saved_to_db_count += 1
                logging.info(f"Image saved for {planet_name}")
        else:
            failed_to_s3_count += 1
            failed_planet_list.append(planet_name)
            logging.warning(f"Image generation failed for {planet_name}")

    conn.close()
    return {
        "total_planets": total_planet_count,
        "saved_to_s3": saved_to_s3_count,
        "failed_to_s3": failed_to_s3_count,
        "s3_success_rate": ((saved_to_s3_count / total_planet_count) * 100),
        "saved_to_db": saved_to_db_count,
        "failed_to_db": failed_to_db_count,
        "failed_planets": failed_planet_list,
        "db_success_rate": ((saved_to_db_count / total_planet_count) * 100),
    }


if __name__ == "__main__":
    result = main()
    print(result)
