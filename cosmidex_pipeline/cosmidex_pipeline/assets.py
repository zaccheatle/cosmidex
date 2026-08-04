"""Dagster asset definitions for the NASA exoplanet ingestion pipeline: extract,
validate, hash-check, load to Bronze, and audit-log.
"""

import hashlib
import logging
import os
import sys

import pandas as pd
import sqlalchemy
from dagster import asset
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from cosmidex_pipeline.models import ExoplanetRecord, validate_records
from src.db_loader import load_db
from src.exoplanet_extractor import build_query

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

PIPELINE_NAME = "nasa_exoplanets"


def _get_engine() -> sqlalchemy.engine.Engine:
    """Build a SQLAlchemy engine for the Postgres instance from env vars.

    Returns:
        sqlalchemy.engine.Engine: Engine connected to the configured Postgres database.
    """
    conn_string = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    return sqlalchemy.create_engine(conn_string)


@asset
def raw_nasa_data() -> pd.DataFrame:
    """Extract raw exoplanet data from NASA TAP service.

    Returns:
        pd.DataFrame: Raw PSCompPars exoplanet records.

    Raises:
        Exception: If the NASA TAP query returns no data.
    """

    nasa_url = os.environ.get("NASA_URL")
    print(f"Debug nasa_url: {nasa_url}")

    df = build_query(
        base_url=nasa_url,
        response_format="csv",
        custom_query="SELECT * FROM pscomppars",
    )

    if df is None:
        raise Exception("NASA TAP query returned no data")

    return df


@asset
def validated_nasa_dict(raw_nasa_data: pd.DataFrame) -> pd.DataFrame:
    """Validate raw NASA data against ExoplanetRecord dataclass schema.

    Args:
        raw_nasa_data (pd.DataFrame): Raw exoplanet dataframe.

    Returns:
        pd.DataFrame: Dataframe of valid records.

    Raises:
        ValueError: If valid_records is empty.
    """

    valid_records, invalid_records = validate_records(raw_nasa_data, ExoplanetRecord)
    if len(valid_records) == 0:
        raise ValueError("There are 0 valid records to process!!!")

    if len(invalid_records) > 0:
        logging.warning(f"Invalid records: {len(invalid_records)}")

    df = pd.DataFrame(valid_records)
    return df


@asset
def hash_dataframe(validated_nasa_dict: pd.DataFrame) -> str:
    """Hash a DataFrame to detect changes between runs.

    Args:
        validated_nasa_dict (pd.DataFrame): Dataframe with rows to hash.

    Returns:
        str: MD5 hash of the dataframe's contents.
    """

    df_sorted = validated_nasa_dict.sort_values(by="pl_name").reset_index(drop=True)
    hash_values = pd.util.hash_pandas_object(df_sorted).to_numpy()
    return hashlib.md5(hash_values.tobytes()).hexdigest()


@asset
def check_file_hash(validated_nasa_dict: pd.DataFrame, hash_dataframe: str) -> dict:
    """Check if NASA data has changed since the last pipeline run and detect new planets.

    Args:
        validated_nasa_dict (pd.DataFrame): Current validated exoplanet dataframe.
        hash_dataframe (str): Hash of the current validated dataframe.

    Returns:
        dict: {
            "changed" (bool): whether the data differs from the last recorded run,
            "current_hash" (str): hash of the current run,
            "new_planets" (list[str]): pl_name values not present in raw.exoplanets yet,
            "planet_count" (int): row count of the current run,
        }
    """

    engine = _get_engine()

    with engine.connect() as conn:
        row = conn.execute(
            sqlalchemy.text(
                "SELECT last_file_hash FROM raw.pipeline_state WHERE pipeline_name = :name"
            ),
            {"name": PIPELINE_NAME},
        ).fetchone()
        previous_hash = row[0] if row else None
        changed = previous_hash != hash_dataframe

        new_planets: list[str] = []
        if changed:
            exoplanets_table_exists = conn.execute(
                sqlalchemy.text("SELECT to_regclass('raw.exoplanets')")
            ).scalar()

            if exoplanets_table_exists is not None:
                previous_names = {
                    r[0]
                    for r in conn.execute(
                        sqlalchemy.text("SELECT DISTINCT pl_name FROM raw.exoplanets")
                    )
                }
                new_planets = sorted(
                    set(validated_nasa_dict["pl_name"]) - previous_names
                )

    if changed:
        logging.info(
            f"NASA data changed since last run — {len(new_planets)} new planet(s) detected."
        )
    else:
        logging.info("NASA data unchanged since last run — downstream load can be skipped.")

    return {
        "changed": changed,
        "current_hash": hash_dataframe,
        "new_planets": new_planets,
        "planet_count": len(validated_nasa_dict),
    }


@asset
def load_bronze(validated_nasa_dict: pd.DataFrame, check_file_hash: dict) -> dict:
    """Full-reload validated NASA data into raw.exoplanets and record the run in raw.pipeline_state.

    Skips the reload entirely if check_file_hash reported no change since the last run.

    Args:
        validated_nasa_dict (pd.DataFrame): Current validated exoplanet dataframe.
        check_file_hash (dict): Output of check_file_hash.

    Returns:
        dict: check_file_hash payload, augmented with "loaded" (bool).
    """

    if not check_file_hash["changed"]:
        logging.info("Skipping Bronze load — NASA data unchanged since last run.")
        return {**check_file_hash, "loaded": False}

    engine = _get_engine()

    with engine.begin() as conn:
        conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS raw.exoplanets CASCADE"))

    df_to_load = validated_nasa_dict.copy()
    df_to_load["loaded_at"] = pd.Timestamp.now()

    load_db(df_to_load, schema_name="raw", table_name="exoplanets")

    with engine.begin() as conn:
        conn.execute(
            sqlalchemy.text(
                """
                INSERT INTO raw.pipeline_state
                    (pipeline_name, last_file_hash, last_run_timestamp, last_planet_count)
                VALUES (:name, :hash, now(), :count)
                ON CONFLICT (pipeline_name) DO UPDATE SET
                    last_file_hash = EXCLUDED.last_file_hash,
                    last_run_timestamp = EXCLUDED.last_run_timestamp,
                    last_planet_count = EXCLUDED.last_planet_count
                """
            ),
            {
                "name": PIPELINE_NAME,
                "hash": check_file_hash["current_hash"],
                "count": check_file_hash["planet_count"],
            },
        )

    if check_file_hash["new_planets"]:
        logging.info(f"New planets detected: {check_file_hash['new_planets']}")

    logging.info(f"Loaded {check_file_hash['planet_count']} rows to raw.exoplanets.")

    return {**check_file_hash, "loaded": True}


@asset
def audit_log(load_bronze: dict) -> None:
    """Write run metadata for this pipeline execution to raw.pipeline_audit.

    Args:
        load_bronze (dict): Output of load_bronze (changed/current_hash/new_planets/planet_count/loaded).

    Returns:
        None.
    """

    engine = _get_engine()

    with engine.begin() as conn:
        conn.execute(
            sqlalchemy.text(
                """
                INSERT INTO raw.pipeline_audit
                    (pipeline_name, changed, loaded, planet_count, new_planet_count, new_planets)
                VALUES (:name, :changed, :loaded, :planet_count, :new_planet_count, :new_planets)
                """
            ),
            {
                "name": PIPELINE_NAME,
                "changed": load_bronze["changed"],
                "loaded": load_bronze["loaded"],
                "planet_count": load_bronze["planet_count"],
                "new_planet_count": len(load_bronze["new_planets"]),
                "new_planets": load_bronze["new_planets"],
            },
        )

    logging.info(
        f"Audit log written — changed: {load_bronze['changed']}, "
        f"loaded: {load_bronze['loaded']}, planet_count: {load_bronze['planet_count']}, "
        f"new_planets: {len(load_bronze['new_planets'])}."
    )
