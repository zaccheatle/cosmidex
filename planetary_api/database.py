"""
Planetary data database connection for API layer
"""

# Import dependencies
import logging
import os
from typing import Any

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


def test_connection() -> bool:
    """Test and validate db connection.

    Args:
        None.

    Returns:
        bool: true or false if connection is established.

    Raises:
        DatabaseError: Psycopg2 database connection error.
    """
    try:
        conn = psycopg2.connect(**connection_params)
        conn.close()
        logging.debug("Database connection succesful!!")
        return True
    except psycopg2.DatabaseError as e:
        logging.error(f"Connection failed: {e}")
        return False


def get_db() -> Any | None:
    """Create a db connection.

    Args:
        None.

    Returns:
        None.

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
