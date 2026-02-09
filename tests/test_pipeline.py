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
            base_url=base_url, table_name="pscomppars", format="csv", columns=["*"]
        )

        # Basic sanity checks
        assert result
        assert len(result) > 0
        assert "pl_name" in result
