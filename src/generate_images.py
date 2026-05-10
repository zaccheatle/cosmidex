"""
Planetary data script to connect to openai api to generate planet images
"""

# import dependencies
import json
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
from psycopg2.extensions import connection as PGConnection

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from cosmidex_api.database import connection_params

load_dotenv()

# initialize s3 client
s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION"))

# initialize openai client
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# set up logger
logging.basicConfig(level=logging.INFO)


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
                planet_name,
                image_prompt
            FROM marts.mart_planet_image_prompt
            WHERE habitability_tier IN ('Tier 1')
            LIMIT 3
        """)
        rows = cursor.fetchall()
        cursor.close()
        return list(rows)

    except psycopg2.DatabaseError as e:
        logging.error(f"Query failed: {e}")
        return []


# # initialize openai client
# def generate_images(prompt: str) -> bytes | None:
#     """Generate planet image using AI prompt.

#     Pass an image prompt to generate an AI image url.

#     Args:
#         prompt (str): Image prompt describing a planets characteristics.

#     Returns:
#         tuple (image_url, image_bytes): Returns the generated image url and image bytes.

#     Raises:
#         Exception: Error generating the image_url.
#     """
#     try:
#         response = client.images.generate(
#             model="gpt-image-1-mini",
#             prompt=prompt,
#             size="1024x1024",
#             quality="medium",
#             n=1,
#         )
#         image_bytes = base64.b64decode(response.data[0].b64_json)  # type: ignore
#         return image_bytes
#     except Exception as e:
#         logging.error(f"Image generation error: {e}")
#         return None


def generate_images(prompt: str) -> bytes | None:
    """Generate planet image using ComfyUI + Juggernaut XL.

    Loads a ComfyUI workflow JSON, injects the planet prompt,
    submits to ComfyUI API, polls until complete, and returns image bytes.

    Args:
        prompt (str): Image prompt describing a planet's characteristics.

    Returns:
        bytes | None: Raw image bytes or None on failure.
    """
    try:
        # load workflow
        workflow_path = os.getenv("COMFY_WORKFLOW_PATH")
        if not workflow_path:
            logging.error("COMFY_WORKFLOW_PATH not set in environment")
            return None

        with open(workflow_path, "r") as f:
            workflow = json.load(f)

        # inject prompt into correct node
        # update this key once you identify the correct node ID from exported JSON
        prompt_node_id = os.getenv("COMFY_PROMPT_NODE_ID", "6")
        workflow[prompt_node_id]["inputs"]["text"] = prompt

        # submit to comfyui
        comfy_url = os.getenv("COMFY_URL", "http://localhost:8000")
        payload = {"prompt": workflow}
        response = requests.post(f"{comfy_url}/prompt", json=payload)
        response.raise_for_status()
        prompt_id = response.json()["prompt_id"]

        # poll until complete
        max_attempts = 60
        for attempt in range(max_attempts):
            time.sleep(3)
            history_response = requests.get(f"{comfy_url}/history/{prompt_id}")
            history = history_response.json()

            if prompt_id in history:
                outputs = history[prompt_id]["outputs"]
                # find first image output across all nodes
                for node_id, node_output in outputs.items():
                    if "images" in node_output:
                        filename = node_output["images"][0]["filename"]
                        subfolder = node_output["images"][0].get("subfolder", "")

                        # fetch image bytes
                        params = {
                            "filename": filename,
                            "subfolder": subfolder,
                            "type": "output",
                        }
                        image_response = requests.get(
                            f"{comfy_url}/view", params=params
                        )
                        image_response.raise_for_status()
                        return image_response.content

            logging.info(f"Waiting for ComfyUI... attempt {attempt + 1}/{max_attempts}")

        logging.error(f"ComfyUI timed out after {max_attempts} attempts")
        return None

    except Exception as e:
        logging.error(f"ComfyUI image generation error: {e}")
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
    """Store S3 url of planet image to db.

    Args:
        conn (PGConnection): Postgres db connection.
        planet_name (str): Planet's name.
        image_url (str): S3 url of image's location.
        prompt (str): Image prompt describing the planets characteristics.
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
        time.sleep(5)
        if result is not None:
            s3_url = upload_to_s3(result, planet_name)
            if s3_url is not None:
                saved_to_s3_count += 1
                logging.info("Image successfully uploaded to s3!")
                save_image(conn, planet_name, s3_url, prompt, "comfyui-juggernaut-xl")
                saved_to_db_count += 1
                logging.info("Image S3 location saved to db.")
            else:
                failed_to_s3_count += 1
                failed_planet_list.append(planet_name)
                logging.warning(f"S3 upload failed for {planet_name}")
        else:
            failed_to_s3_count += 1
            failed_planet_list.append(planet_name)
            logging.warning(f"Image generation failed for {planet_name}")

    conn.close()
    return {
        "total_planets": total_planet_count,
        "saved_to_s3": saved_to_s3_count,
        "failed_to_s3": failed_to_s3_count,
        "s3_success_rate": f"{(saved_to_s3_count / total_planet_count * 100):.1f}%"
        if total_planet_count > 0
        else "N/A",
        "saved_to_db": saved_to_db_count,
        "failed_to_db": failed_to_db_count,
    }


if __name__ == "__main__":
    result = main()
    logging.info(f"Pipeline complete: {result}")
