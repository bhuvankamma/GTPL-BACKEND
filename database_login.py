import psycopg2
from contextlib import contextmanager
from utils.config_login import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT


@contextmanager
def get_db_conn():
    conn = psycopg2.connect(
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    try:
        yield conn
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()
