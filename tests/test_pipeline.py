"""
Docstring for pipeline
"""

# Import dependencies
import os

from dotenv import load_dotenv

from src.planet_extractor import build_query

# Load env variables
load_dotenv()

# Load NASA TAP URLS Dict from env variables
base_url = os.environ.get("NASA_URL")


# Run pipeline
def test_build_query():
    if base_url:
        result = build_query(
            base_url=base_url,
            format="csv",
            table_name="pscomppars",
            columns=[
                "pl_name",
                "hostname",
                "pl_rade",
                "pl_bmasse",
                "pl_eqt",
                "pl_orbper",
                "pl_orbsmax",
                "st_teff",
                "st_spectype",
                "st_rad",
                "st_mass",
                "sy_dist",
                "disc_year",
                "discoverymethod",
                "default_flag",
            ],
        )

        # Basic sanity checks
        assert result is not None
        assert len(result) > 0
