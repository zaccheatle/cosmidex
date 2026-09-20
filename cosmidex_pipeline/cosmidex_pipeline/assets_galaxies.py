"""Dagster asset definitions for the OpenNGC ingestion pipeline: extract,
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

from cosmidex_pipeline.models import GalaxyRecord, validate_records
from cosmidex_pipeline.utils import get_engine
from src.db_loader import load_db

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

PIPELINE_NAME = "openngc"


@asset(group_name="galaxies")
def raw_data() -> pd.DataFrame:
    """Download raw dataset.

    Returns:
        df (pd.DataFrame): Dataframe of raw records.

    Raises:
        FileNotFoundError
        EmptyDataError
        ParserError
        UnicodeDecodeError
        Exception
    """

    openngc_url = os.environ.get("OPENNGC_URL")
    logging.debug(f"Debug openngc_url: {openngc_url}")

    if openngc_url:
        try:
            df = pd.read_csv(openngc_url, sep=";", encoding="utf-8")
            df = df.rename(columns=str.lower)
            return df

        except FileNotFoundError:
            logging.error("Error: The specified file was not found.")
            raise

        except pd.errors.EmptyDataError:
            logging.error("Error: The CSV file is empty.")
            raise

        except pd.errors.ParserError:
            logging.error(
                "Error: The CSV has parsing issues (e.g., mismatched columns or bad rows)."
            )
            raise

        except UnicodeDecodeError:
            logging.error(
                "Error: Encoding issue. Try adding encoding='latin1' or encoding='utf-8-sig'."
            )
            raise

        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            raise
    else:
        raise ValueError("OPENNGC_URL is not set")


@asset(group_name="galaxies")
def validated_dict(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Validate raw data against dataclass schema.

    Args:
        raw_data (pd.DataFrame): Raw dataframe.

    Returns:
        pd.DataFrame: Dataframe of valid records.

    Raises:
        ValueError: If valid_records is empty.
    """

    valid_records, invalid_records = validate_records(raw_data, GalaxyRecord)
    if len(valid_records) == 0:
        raise ValueError("There are 0 valid records to process!!!")

    if len(invalid_records) > 0:
        logging.warning(f"Invalid records: {len(invalid_records)}")

    df = pd.DataFrame(valid_records)
    return df


@asset(group_name="galaxies")
def galaxies_hash_dataframe(validated_dict: pd.DataFrame) -> str:
    """Hash a DataFrame to detect changes between runs.

    Args:
        validated_dict (pd.DataFrame): Dataframe with rows to hash.

    Returns:
        str: MD5 hash of the dataframe's contents.
    """

    df_sorted = validated_dict.sort_values(by="name").reset_index(drop=True)
    hash_values = pd.util.hash_pandas_object(df_sorted).to_numpy()
    return hashlib.md5(hash_values.tobytes()).hexdigest()


@asset(group_name="galaxies")
def galaxies_check_file_hash(
    validated_dict: pd.DataFrame, galaxies_hash_dataframe: str
) -> dict:
    """Check if data has changed since the last pipeline run and detect new records.

    Args:
        validated_dict (pd.DataFrame): Current validated dataframe.
        galaxies_hash_dataframe (str): Hash of the current validated dataframe.

    Returns:
        dict: {
            "changed" (bool): whether the data differs from the last recorded run,
            "current_hash" (str): hash of the current run,
            "new_records" (list[str]): pk values not present in raw dbt model yet,
            "record_count" (int): row count of the current run
        }
    """

    engine = get_engine()

    with engine.connect() as conn:
        row = conn.execute(
            sqlalchemy.text(
                "SELECT last_file_hash FROM raw.pipeline_state WHERE pipeline_name = :name"
            ),
            {"name": PIPELINE_NAME},
        ).fetchone()
        previous_hash = row[0] if row else None
        changed = previous_hash != galaxies_hash_dataframe

        new_records: list[str] = []
        if changed:
            exorecords_table_exists = conn.execute(
                sqlalchemy.text("SELECT to_regclass('raw.ngc_objects')")
            ).scalar()

            if exorecords_table_exists is not None:
                previous_names = {
                    r[0]
                    for r in conn.execute(
                        sqlalchemy.text("SELECT DISTINCT name FROM raw.ngc_objects")
                    )
                }
                new_records = sorted(set(validated_dict["name"]) - previous_names)

    if changed:
        logging.info(
            f"Data changed since last run — {len(new_records)} new record(s) detected."
        )
    else:
        logging.info("Data unchanged since last run — downstream load can be skipped.")

    return {
        "changed": changed,
        "current_hash": galaxies_hash_dataframe,
        "new_records": new_records,
        "record_count": len(validated_dict),
    }


@asset(group_name="galaxies")
def galaxies_load_bronze(
    validated_dict: pd.DataFrame, galaxies_check_file_hash: dict
) -> dict:
    """Full-reload validated Data into raw.ngc_objects and record the run in raw.pipeline_state.

    Skips the reload entirely if galaxies_check_file_hash reported no change since the last run.

    Args:
        validated_dict (pd.DataFrame): Current validated dataframe.
        galaxies_check_file_hash (dict): Output of galaxies_check_file_hash.

    Returns:
        dict: galaxies_check_file_hash payload, augmented with "loaded" (bool).
    """

    if not galaxies_check_file_hash["changed"]:
        logging.info("Skipping Bronze load — Data unchanged since last run.")
        return {**galaxies_check_file_hash, "loaded": False}

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS raw.ngc_objects CASCADE"))

    df_to_load = validated_dict.copy()
    df_to_load["loaded_at"] = pd.Timestamp.now()

    load_db(df_to_load, schema_name="raw", table_name="ngc_objects")

    with engine.begin() as conn:
        conn.execute(
            sqlalchemy.text(
                """
                INSERT INTO raw.pipeline_state
                    (pipeline_name, last_file_hash, last_run_timestamp, last_record_count)
                VALUES (:name, :hash, now(), :count)
                ON CONFLICT (pipeline_name) DO UPDATE SET
                    last_file_hash = EXCLUDED.last_file_hash,
                    last_run_timestamp = EXCLUDED.last_run_timestamp,
                    last_record_count = EXCLUDED.last_record_count
                """
            ),
            {
                "name": PIPELINE_NAME,
                "hash": galaxies_check_file_hash["current_hash"],
                "count": galaxies_check_file_hash["record_count"],
            },
        )

    if galaxies_check_file_hash["new_records"]:
        logging.info(f"New records detected: {galaxies_check_file_hash['new_records']}")

    logging.info(
        f"Loaded {galaxies_check_file_hash['record_count']} rows to raw.ngc_objects."
    )

    return {**galaxies_check_file_hash, "loaded": True}


@asset(group_name="galaxies")
def galaxies_audit_log(galaxies_load_bronze: dict) -> None:
    """Write run metadata for this pipeline execution to raw.pipeline_audit.

    Args:
        galaxies_load_bronze (dict): Output of galaxies_load_bronze
            (changed/current_hash/new_records/record_count/loaded).

    Returns:
        None.
    """

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(
            sqlalchemy.text(
                """
                INSERT INTO raw.pipeline_audit
                    (pipeline_name, changed, loaded, record_count, new_record_count, new_records)
                VALUES (:name, :changed, :loaded, :record_count, :new_record_count, :new_records)
                """
            ),
            {
                "name": PIPELINE_NAME,
                "changed": galaxies_load_bronze["changed"],
                "loaded": galaxies_load_bronze["loaded"],
                "record_count": galaxies_load_bronze["record_count"],
                "new_record_count": len(galaxies_load_bronze["new_records"]),
                "new_records": galaxies_load_bronze["new_records"],
            },
        )

    logging.info(
        f"Audit log written — changed: {galaxies_load_bronze['changed']}, "
        f"loaded: {galaxies_load_bronze['loaded']}, record_count: {galaxies_load_bronze['record_count']}, "
        f"new_records: {len(galaxies_load_bronze['new_records'])}."
    )
