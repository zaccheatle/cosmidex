"""
Module for executing the cosmidex data pipeline end to end.
"""

# Import dependencies
import os

from dotenv import load_dotenv

from db_loader import load_db
from exoplanet_extractor import build_query
from hwc_extractor import scrape_hwc

load_dotenv()

# Load NASA TAP URLS Dict from env variables
nasa_url = os.environ.get("NASA_URL")
hwc_url = os.environ.get("HWC_URL")


# Run pipeline
def run_pipeline():
    """Execute cosmidex pipeline."""

    # Extract and load HWC habitable planet dataset
    if hwc_url:
        hwc_df = scrape_hwc(hwc_url)

        if hwc_df is not None and not hwc_df.empty:
            load_db(hwc_df, schema_name="raw", table_name="hwc")

    # Extract and load NASA exoplanet dataset
    if nasa_url:
        nasa_df = build_query(
            base_url=nasa_url,
            format="csv",
            custom_query="SELECT * FROM pscomppars",
        )

        if nasa_df is not None and not nasa_df.empty:
            load_db(nasa_df, schema_name="raw", table_name="exoplanets")


if __name__ == "__main__":
    run_pipeline()
