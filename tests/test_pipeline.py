"""
Docstring for pipeline test
"""

# Import dependencies
import os

from dotenv import load_dotenv

from src.planet_extractor import build_query
from src.planet_loader import load_db

load_dotenv()

# Load NASA TAP URLS Dict from env variables
base_url = os.environ.get("NASA_URL")


# Run pipeline
def test_build_query():
    """Test planet pipeline"""
    if base_url:
        result = build_query(
            base_url=base_url,
            format="csv",
            table_name="pscomppars",
            columns=[],
            custom_query="SELECT * FROM pscomppars",
        )

        # Basic sanity checks
        assert result is not None
        assert len(result) > 0

        load_db(result, schema_name="raw", table_name="exoplanets")
