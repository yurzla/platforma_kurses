# подключение к PostgreSQL
import psycopg
from app.core.config import DSN

def get_connection():
    if not DSN:
        raise RuntimeError("Не задан DSN для подключения к PostgreSQL.")
    return psycopg.connect(DSN)