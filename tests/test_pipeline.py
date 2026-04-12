"""
Docstring for pipeline test
"""

# Import dependencies
import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.exoplanet_extractor import build_query
from src.db_loader import load_db

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
