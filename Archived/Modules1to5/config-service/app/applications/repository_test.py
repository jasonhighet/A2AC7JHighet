"""
app/applications/repository_test.py
------------------------------------
Unit tests for ApplicationRepository using mocked psycopg2 connections.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.applications.repository import ApplicationRepository
from app.exceptions import DuplicateNameError, NotFoundError
import psycopg2


def make_mock_conn(rows=None, description=None):
    """Helper: returns a mock psycopg2 connection."""
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.fetchone.return_value = rows[0] if rows else None
    mock_cursor.fetchall.return_value = rows or []
    mock_cursor.description = description or [
        ("id",), ("name",), ("comments",)
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


def test_create_returns_dict():
    row = ("01ARZ3NDEKTSV4RRFFQ69G5FAV", "my-app", None)
    mock_conn, mock_cursor = make_mock_conn(rows=[row])

    with patch("app.applications.repository.ULID", return_value="01ARZ3NDEKTSV4RRFFQ69G5FAV"):
        repo = ApplicationRepository()
        result = repo.create(mock_conn, name="my-app", comments=None)

    assert result["id"] == "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    assert result["name"] == "my-app"
    mock_conn.commit.assert_called_once()


def test_create_raises_on_duplicate():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    mock_cursor.execute.side_effect = psycopg2.errors.UniqueViolation()
    mock_conn.cursor.return_value = mock_cursor

    repo = ApplicationRepository()
    with pytest.raises(DuplicateNameError):
        repo.create(mock_conn, name="duplicate", comments=None)
    mock_conn.rollback.assert_called_once()


def test_get_by_id_raises_not_found():
    mock_conn, mock_cursor = make_mock_conn(rows=[])
    mock_cursor.fetchone.return_value = None

    repo = ApplicationRepository()
    with pytest.raises(NotFoundError):
        repo.get_by_id(mock_conn, id="nonexistent")


def test_list_all_returns_list():
    rows = [
        ("id1", "app-a", None),
        ("id2", "app-b", "A comment"),
    ]
    mock_conn, _ = make_mock_conn(rows=rows)

    repo = ApplicationRepository()
    result = repo.list_all(mock_conn)

    assert len(result) == 2
    assert result[0]["name"] == "app-a"
