"""
app/database_test.py
--------------------
Tests for the database connection helper.
"""

import pytest
from unittest.mock import patch, MagicMock


def test_get_connection_yields_connection():
    """get_connection() should yield a usable connection object."""
    mock_conn = MagicMock()
    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    import app.database as db_module

    original_pool = db_module._pool
    db_module._pool = mock_pool
    try:
        with db_module.get_connection() as conn:
            assert conn is mock_conn
        mock_pool.putconn.assert_called_once_with(mock_conn)
    finally:
        db_module._pool = original_pool


def test_get_connection_returns_on_exception():
    """Connection must be returned to pool even if an exception is raised."""
    mock_conn = MagicMock()
    mock_pool = MagicMock()
    mock_pool.getconn.return_value = mock_conn

    import app.database as db_module

    original_pool = db_module._pool
    db_module._pool = mock_pool
    try:
        with pytest.raises(ValueError):
            with db_module.get_connection() as conn:
                raise ValueError("boom")
        mock_pool.putconn.assert_called_once_with(mock_conn)
        mock_conn.rollback.assert_called_once()
    finally:
        db_module._pool = original_pool
