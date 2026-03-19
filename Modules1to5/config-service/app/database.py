"""
app/database.py
---------------
PostgreSQL connection pool and context manager.

Usage in repository methods:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT ...")
"""

from contextlib import contextmanager
from typing import Generator

import psycopg2
import psycopg2.extras
import psycopg2.pool

from app.config import settings

_pool: psycopg2.pool.ThreadedConnectionPool | None = None


def _get_pool() -> psycopg2.pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=settings.database_url,
        )
    return _pool


def init_pool(database_url: str | None = None) -> None:
    """Explicitly initialise (or re-initialise) the connection pool.
    Useful in tests to point at the test database."""
    global _pool
    if _pool is not None:
        _pool.closeall()
    dsn = database_url or settings.database_url
    _pool = psycopg2.pool.ThreadedConnectionPool(minconn=1, maxconn=10, dsn=dsn)


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


@contextmanager
def get_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """Yield a psycopg2 connection from the pool; return it on exit."""
    pool = _get_pool()
    conn = pool.getconn()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)
