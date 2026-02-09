"""
Docstring for planet_extractor
"""

# Import dependencies
import logging
from io import StringIO
from typing import Any, Literal

import pandas as pd
import requests
from astropy.io.votable import parse


# Function to buld TAP query
def build_query(
    base_url: str,
    table_name: str,
    format: Literal["csv", "json", "tsv", "VOTable"],
    columns: list[str] = ["*"],
) -> Any | None:
    """
    Docstring for build_query

    :param base_url: Description
    :type base_url: str
    :param table_name: Description
    :type table_name: str
    :param format: Description
    :type format: Literal["csv", "json", "tsv", "VOTable"]
    :param columns: Description
    :type columns: list[str]
    :return: Description
    :rtype: Any | None
    """

    if not base_url:
        raise ValueError("base_url is missing!")
    elif not table_name:
        raise ValueError("table_name is missing!")
    elif base_url and table_name:
        # Build SQL query
        cols = ", ".join(columns) if columns != ["*"] else "*"
        query = f"SELECT {cols} FROM {table_name}"

        # Make request with parameters
        params = {"query": query, "format": format}

        response = requests.get(base_url, params=params)
        if response:
            logging.info("Response successfull, processing..")
            try:
                if format == "json":
                    return response.json()

                elif format == "csv":
                    return pd.read_csv(StringIO(response.text))

                elif format == "tsv":
                    return pd.read_csv(StringIO(response.text), sep="\t")

                elif format == "votable":
                    votable = parse(response.content)
                    table = votable.get_first_table()
                    return table.to_table()

            except Exception as e:
                logging.error(f"Error parsing {format} response: {e}")
                raise
        else:
            response.raise_for_status()
