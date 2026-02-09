# import dependencies
import logging
import os
from typing import Any

import psycopg2
from dotenv import load_dotenv

# set log level
logging.basicConfig(level=logging.DEBUG)

# set env variables
load_dotenv()


# test db connection
def test_connection() -> Any | None:
    """
    Docstring for test_connection

    :return: Description
    :rtype: Any | None
    """

    # initialize conn
    conn = None
    try:
        logging.debug("Connecting to databse....")
        conn = psycopg2.connect(
            host="127.0.0.1",
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            port=5433,
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
