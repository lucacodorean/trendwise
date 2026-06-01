from collections.abc import Iterator
from contextlib import contextmanager

import psycopg

from app.core.config import settings


@contextmanager
def open_database_connection() -> Iterator[psycopg.Connection]:
    connection = psycopg.connect(settings.database_url)
    try:
        yield connection
    finally:
        connection.close()
