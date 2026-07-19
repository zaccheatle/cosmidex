import logging
import os
import sys

import pandas as pd
from dagster import asset
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from cosmidex_pipeline.models import ExoplanetRecord, validate_records
from src.exoplanet_extractor import build_query

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)


@asset
def raw_nasa_data() -> pd.DataFrame:
    """Extract raw exoplanet data from NASA TAP service."""

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
    """
    Validate raw NASA data against ExoplanetRecord dataclass schema.

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
