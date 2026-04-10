""""""

# import dependencies
import os

from dotenv import load_dotenv

from exoplanet_extractor import build_query
from exoplanet_loader import load_db

load_dotenv()

# Load NASA TAP URLS Dict from env variables
base_url = os.environ.get("NASA_URL")


# Run pipeline
def run_pipeline():
    """"""
    if base_url:
        df = build_query(
            base_url=base_url,
            format="csv",
            custom_query="SELECT * FROM pscomppars",
        )

        if df is not None and not df.empty:
            load_db(df, schema_name="raw", table_name="exoplanets")


if __name__ == "__main__":
    run_pipeline()
