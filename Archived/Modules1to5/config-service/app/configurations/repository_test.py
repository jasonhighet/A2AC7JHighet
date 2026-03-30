"""
app/configurations/repository_test.py
--------------------------------------
Unit tests for ConfigurationRepository using mocked psycopg2 connections.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.configurations.repository import ConfigurationRepository
from app.exceptions import NotFoundError


def make_mock_conn(rows=None):
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchone.return_value = rows[0] if rows else None
    mock_cursor.fetchall.return_value = rows or []
    mock_cursor.description = [
        ("id",), ("application_id",), ("name",), ("comments",), ("config",)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


def test_create_returns_dict():
    row = ("01ID", "01APPID", "prod", None, {"db": "localhost"})
    mock_conn, _ = make_mock_conn(rows=[row])

    with patch("app.configurations.repository.ULID", return_value="01ID"):
        repo = ConfigurationRepository()
        result = repo.create(
            mock_conn,
            application_id="01APPID",
            name="prod",
            comments=None,
            config={"db": "localhost"},
        )

    assert result["id"] == "01ID"
    assert result["name"] == "prod"
    mock_conn.commit.assert_called_once()


def test_get_by_id_raises_not_found():
    mock_conn, mock_cursor = make_mock_conn(rows=[])
    mock_cursor.fetchone.return_value = None

    repo = ConfigurationRepository()
    with pytest.raises(NotFoundError):
        repo.get_by_id(mock_conn, id="missing")
