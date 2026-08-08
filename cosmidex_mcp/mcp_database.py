"""Database connection management for the CosmiDex MCP server.

Provides `db_connection`, a context-manager wrapper around a psycopg2
connection to the CosmiDex Postgres database, for use by MCP tool functions
that need to query cosmic data.
"""

import logging
import os
from contextlib import contextmanager
from decimal import Decimal
from typing import Any, Generator

import psycopg2
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)

load_dotenv()


connection_params = {
    "host": os.getenv("POSTGRES_HOST"),
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "sslmode": "disable",
}


@contextmanager
def db_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """Create a db connection for MCP.

    Yields:
        connection: An open psycopg2 database connection.

    Raises:
        DatabaseError: Psycopg2 database connection error.
    """
    conn = None
    try:
        conn = psycopg2.connect(**connection_params)
        logging.debug("Database connection successful")
        yield conn
    except psycopg2.DatabaseError as e:
        logging.error(f"Connection failed: {e}")
        raise
    finally:
        if conn is not None:
            conn.close()
            logging.debug("Database connection closed")


def numeric_handler(row: dict) -> dict[str, Any]:
    """Helper function to convert db rows.

    Args:
        row (dict): A database row.

    Returns:
        clean_row (dict): cleaned row.
    """

    clean_row = {k: (float(v) if isinstance(v, Decimal) else v) for k, v in row.items()}
    logging.info("Row cleaned successfully.")
    return clean_row
