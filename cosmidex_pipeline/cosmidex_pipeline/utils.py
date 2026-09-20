"""
Shared modules and helper functions for dagster pipelines
"""

import os

import sqlalchemy
from dotenv import load_dotenv

load_dotenv()


def get_engine() -> sqlalchemy.engine.Engine:
    """Build a SQLAlchemy engine for the Postgres instance from env vars.

    Returns:
        sqlalchemy.engine.Engine: Engine connected to the configured Postgres database.
    """
    conn_string = (
        f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )
    return sqlalchemy.create_engine(conn_string)
