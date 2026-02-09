"""
Docstring for planet_extractor
"""

# import dependencies
import logging
from io import StringIO
from typing import Any, Literal

import pandas as pd
import requests
from astropy.io.votable import parse

# Dict of available NASA data urls to run TAP queries with
base_urls = {
    "NASA Exoplanet endpoint": "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query="
}


# Function to buld TAP query
def build_query(
    base_url: str,
    table_name: str,
    format: Literal["csv", "json", "tsv", "VOTable"],
    columns: list[str] = ["*"],
) -> Any | None:

    if not base_url:
        raise ValueError("base_url is missing!")
    if not table_name:
        raise ValueError("table_name is missing!")
    if base_url and table_name:
        # Build SQL query
        cols = ", ".join(columns) if columns != ["*"] else "*"
        query = f"SELECT {cols} FROM {table_name}"

        # Make request with parameters
        params = {"query": query, "format": format}

        try:
            response = requests.get(base_url, params=params)

            logging.info(
                f"desired output format is: {format}, parsing appropriately..."
            )
            if format == "json":
                data = response.json()
            if format == "csv":
                data = pd.read_csv(response.text)
            if format == "tsv":
                data = pd.read_csv(StringIO(response.text), sep="\t")
            if format == "VOTable":
                votable = parse(response.content)
                table = votable.get_first_table()
                data = table.to_table()

            return data

        except Exception as e:
            logging.error(f"Error querying data: {e}")
