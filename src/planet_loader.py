"""
Docstring for planet_loader
"""

# Import dependencies
import logging
import os
from typing import Any

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2 import extras, sql

# set log level
logging.basicConfig(level=logging.DEBUG)

# set env variables
load_dotenv()


# Upsert into db
def load_db(data: pd.DataFrame, schema_name: str, table_name: str) -> Any:
    """
    Docstring for load_db

    :param data: Description
    :type data: pd.DataFrame
    :param schema_name: Description
    :type schema_name: str
    :param table_name: Description
    :type table_name: str
    :return: Description
    :rtype: Any
    """

    data_to_upsert = list(data.itertuples(index=False, name=None))

    try:
        logging.debug("Connecting to database....")
        with psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            port=os.getenv("POSTGRES_PORT"),
            sslmode="disable",
        ) as conn:
            logging.info("Connection successful!")

            with conn.cursor() as cur:  # Cursor context manager
                upsert_query = sql.SQL("""
                    INSERT INTO {}.{} (
                        pl_name, hostname, pl_rade, pl_bmasse, pl_eqt, pl_orbper, 
                        pl_orbsmax, st_teff, st_spectype, st_rad, st_mass, sy_dist, 
                        disc_year, discoverymethod, default_flag
                    ) VALUES %s
                    ON CONFLICT (pl_name) 
                    DO UPDATE SET
                        hostname = EXCLUDED.hostname,
                        pl_rade = EXCLUDED.pl_rade,
                        pl_bmasse = EXCLUDED.pl_bmasse,
                        pl_eqt = EXCLUDED.pl_eqt,
                        pl_orbper = EXCLUDED.pl_orbper,
                        pl_orbsmax = EXCLUDED.pl_orbsmax,
                        st_teff = EXCLUDED.st_teff,
                        st_spectype = EXCLUDED.st_spectype,
                        st_rad = EXCLUDED.st_rad,
                        st_mass = EXCLUDED.st_mass,
                        sy_dist = EXCLUDED.sy_dist,
                        disc_year = EXCLUDED.disc_year,
                        discoverymethod = EXCLUDED.discoverymethod,
                        default_flag = EXCLUDED.default_flag
                """).format(
                    sql.Identifier(schema_name),
                    sql.Identifier(table_name),
                )

                extras.execute_values(cur, upsert_query, data_to_upsert, page_size=1000)

            conn.commit()
            logging.info(f"Bulk upsert successful for {len(data_to_upsert)} rows.")

    except psycopg2.Error as e:
        logging.error(f"Database error: {e}")
        raise
