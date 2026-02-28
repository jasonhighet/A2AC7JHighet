"""
app/applications/service_test.py
---------------------------------
Unit tests for the applications service layer.
Repository is mocked so no DB connection is needed.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.applications.models import ApplicationCreate, ApplicationUpdate


@patch("app.applications.service.get_connection")
@patch("app.applications.service._repo")
def test_create_application(mock_repo, mock_get_conn):
    mock_conn = MagicMock()
    mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
    mock_repo.create.return_value = {"id": "01ID", "name": "my-app", "comments": None}

    from app.applications.service import create_application
    result = create_application(ApplicationCreate(name="my-app"))

    assert result.name == "my-app"
    mock_repo.create.assert_called_once_with(mock_conn, name="my-app", comments=None)


@patch("app.applications.service.get_connection")
@patch("app.applications.service._repo")
def test_list_applications(mock_repo, mock_get_conn):
    mock_conn = MagicMock()
    mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
    mock_repo.list_all.return_value = [
        {"id": "01A", "name": "app-a", "comments": None},
        {"id": "01B", "name": "app-b", "comments": "note"},
    ]

    from app.applications.service import list_applications
    results = list_applications()

    assert len(results) == 2
    assert results[0].name == "app-a"
