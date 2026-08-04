"""Generic Postgres loader used by the legacy pipeline scripts in src/."""

import logging
import os

import pandas as pd
import sqlalchemy
import sqlalchemy.exc
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)

load_dotenv()


def load_db(data: pd.DataFrame, schema_name: str, table_name: str) -> None:
    """Dynamically load a DataFrame to Postgres, auto-creating the table from its schema.

    Args:
        data (pd.Dataframe): Dataframe of data to be inserted into db.
        schema_name (str): Database schema to use for insert.
        table_name (str): Database table where date will be inserted.

    Returns:
        None.

    Raises:
        SQLAlchemyError: Database error.
    """

    try:
        conn_string = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

        engine = sqlalchemy.create_engine(conn_string)

        data.to_sql(
            name=table_name,
            con=engine,
            schema=schema_name,
            if_exists="replace",  # or 'append' for upserts
            index=False,
            method="multi",
        )

        logging.info(
            f"Successfully loaded {len(data)} rows to {schema_name}.{table_name}"
        )

    except sqlalchemy.exc.SQLAlchemyError as e:
        logging.error(f"Database error: {e}")
        raise
