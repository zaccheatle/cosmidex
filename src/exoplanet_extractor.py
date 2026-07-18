"""
Module for scraping the NASA exoplanet archive's PScomppars dataset.
"""

# Import dependencies
import logging
from io import StringIO
from typing import Literal

import pandas as pd
import requests
from astropy.io.votable import parse


# Function to buld TAP query
def build_query(
    base_url: str | None,
    response_format: Literal["csv", "json", "tsv", "VOTable"],
    table_name: str | None = None,
    columns: list[str] = ["*"],
    custom_query: str | None = None,
) -> pd.DataFrame | None:
    """
    Function to build dynamic queries to programmatically retrieve data from NASA's Exoplanet Archive TAP service.
    Supports both simple table queries and custom ADQL queries for metadata or complex filtering.

    Args:
        base_url: TAP service endpoint URL
        response_format: format (json, csv, tsv, or votable)
        table_name: Table to query (e.g., 'ps' for Planetary Systems). Optional if custom_query is provided.
        columns: List of column names to select. Default is ["*"] for all columns.
        custom_query: Full ADQL query string. If provided, overrides table_name and columns.

    Returns:
        Parsed data in format-specific type:
        - json: dict or list
        - csv/tsv: pandas DataFrame
        - votable: astropy Table

    Raises:
        ValueError: If neither table_name nor custom_query is provided
        requests.HTTPError: If the API request fails

    Examples:
    >>> # Simple query
    >>> data = build_query(url, "json", table_name="ps")

    >>> # Metadata query
    >>> schemas = build_query(url, "json",
    ...     custom_query="SELECT schema_name FROM TAP_SCHEMA.schemas")

    """

    if not base_url:
        raise ValueError("base_url is missing!")
    if custom_query:
        query = custom_query
    elif table_name:
        cols = ", ".join(columns) if columns != ["*"] else "*"
        query = f"SELECT {cols} FROM {table_name}"
    else:
        raise ValueError("Either table_name or custom_query must be provided!")

    params = {"query": query, "format": response_format}
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    logging.info("Response successfull, processing..")
    try:
        if response_format == "json":
            return response.json()

        elif response_format == "csv":
            data = pd.read_csv(StringIO(response.text), low_memory=False)
            return data

        elif response_format == "tsv":
            return pd.read_csv(StringIO(response.text), sep="\t", low_memory=False)

        elif response_format == "votable":
            votable = parse(response.content)
            table = votable.get_first_table()
            return table.to_table()

    except Exception as e:
        logging.error(f"Error parsing {response_format} response: {e}")
        raise
