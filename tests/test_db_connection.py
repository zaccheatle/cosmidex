"""Manual smoke test for the Postgres database connection."""

import logging
import os
from typing import Any

import psycopg2
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)

load_dotenv()


def test_connection() -> Any | None:
    """Test and verify db connection.

    Returns:
        connection | None: An open psycopg2 connection, or None on failure.

    Raises:
        DatabaseError: Psycopg2 database error.
    """

    conn = None
    try:
        logging.debug("Connecting to database....")
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            sslmode="disable",
        )

        cur = conn.cursor()
        cur.execute("SELECT version()")

        cur.close()
        return conn

    except psycopg2.DatabaseError as e:
        print(f"Error connecting to the database: {e}")
        return None

    finally:
        if conn is not None:
            logging.debug("Database connection succesful!!")
            conn.close()
            logging.debug("Database connection closed.")


if __name__ == "__main__":
    test_connection()
