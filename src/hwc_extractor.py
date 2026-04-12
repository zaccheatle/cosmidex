"""
Module for scraping the Habitable Worlds Catalog's potentially habitable exoplanets dataset.
"""

# Import dependencies
import logging

import pandas as pd


# Scrape csv
def scrape_hwc(url: str) -> pd.DataFrame | None:
    """
    Scrape csv of habitable planet data from Habitable Worlds Catalog.

    Args:
        url (str): url for csv dataset.

    Returns:
        df (DataFrame): dataframe of csv data.

    Raises:
        Exception: error saving data to dataframe.
    """
    try:
        df = pd.read_csv(url)
        logging.info("Data saved to dataframe!")
        if df is not None:
            return df
        else:
            return None
    except Exception as e:
        logging.error(f"Error saving url to dataframe: {e}.")
        return None
