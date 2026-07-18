import os
import sys

import pandas as pd
from dagster import asset
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.exoplanet_extractor import build_query

load_dotenv()


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
