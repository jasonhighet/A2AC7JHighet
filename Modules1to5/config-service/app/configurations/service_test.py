"""
app/configurations/service_test.py
------------------------------------
Unit tests for the configurations service layer.
"""

from unittest.mock import MagicMock, patch

from app.configurations.models import ConfigurationCreate, ConfigurationUpdate


@patch("app.configurations.service.get_connection")
@patch("app.configurations.service._repo")
def test_create_configuration(mock_repo, mock_get_conn):
    mock_conn = MagicMock()
    mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
    mock_repo.create.return_value = {
        "id": "01ID",
        "application_id": "01APPID",
        "name": "prod",
        "comments": None,
        "config": {"db": "localhost"},
    }

    from app.configurations.service import create_configuration
    result = create_configuration(
        ConfigurationCreate(application_id="01APPID", name="prod", config={"db": "localhost"})
    )

    assert result.name == "prod"
    assert result.config == {"db": "localhost"}


@patch("app.configurations.service.get_connection")
@patch("app.configurations.service._repo")
def test_get_configuration(mock_repo, mock_get_conn):
    mock_conn = MagicMock()
    mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)
    mock_repo.get_by_id.return_value = {
        "id": "01ID",
        "application_id": "01APPID",
        "name": "prod",
        "comments": None,
        "config": {},
    }

    from app.configurations.service import get_configuration
    result = get_configuration("01ID")

    assert result.id == "01ID"
