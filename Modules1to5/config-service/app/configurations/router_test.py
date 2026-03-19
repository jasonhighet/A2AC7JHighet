"""
app/configurations/router_test.py
----------------------------------
Integration tests for the configurations router.
Service layer is mocked — no DB needed.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch

from app.main import app
from app.configurations.models import ConfigurationResponse
from app.exceptions import NotFoundError

BASE = "/api/v1/configurations"


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_create_configuration(client):
    mock_response = ConfigurationResponse(
        id="01ID",
        application_id="01APPID",
        name="prod",
        comments=None,
        config={"db": "localhost"},
    )
    with patch(
        "app.configurations.router.service.create_configuration",
        return_value=mock_response,
    ):
        resp = await client.post(
            BASE,
            json={"application_id": "01APPID", "name": "prod", "config": {"db": "localhost"}},
        )
    assert resp.status_code == 201
    assert resp.json()["name"] == "prod"
    assert resp.json()["config"] == {"db": "localhost"}


async def test_get_configuration(client):
    mock_response = ConfigurationResponse(
        id="01ID",
        application_id="01APPID",
        name="prod",
        comments=None,
        config={},
    )
    with patch(
        "app.configurations.router.service.get_configuration",
        return_value=mock_response,
    ):
        resp = await client.get(f"{BASE}/01ID")
    assert resp.status_code == 200
    assert resp.json()["id"] == "01ID"


async def test_get_configuration_not_found(client):
    with patch(
        "app.configurations.router.service.get_configuration",
        side_effect=NotFoundError("Configuration", "bad-id"),
    ):
        resp = await client.get(f"{BASE}/bad-id")
    assert resp.status_code == 404


async def test_update_configuration(client):
    mock_response = ConfigurationResponse(
        id="01ID",
        application_id="01APPID",
        name="prod",
        comments=None,
        config={"db": "prod-host"},
    )
    with patch(
        "app.configurations.router.service.update_configuration",
        return_value=mock_response,
    ):
        resp = await client.put(f"{BASE}/01ID", json={"config": {"db": "prod-host"}})
    assert resp.status_code == 200
    assert resp.json()["config"] == {"db": "prod-host"}
