import psycopg2
from psycopg2.extras import RealDictCursor
from backend import config


def get_db_connection():
    conn = psycopg2.connect(
        host=config.DB_HOST,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        port=config.DB_PORT,
        cursor_factory=RealDictCursor
    )
    return conn
