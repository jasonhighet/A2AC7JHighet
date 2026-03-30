"""
app/applications/router_test.py
--------------------------------
Integration tests for the applications router.
Service layer is mocked — no DB needed.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch

from app.main import app
from app.applications.models import ApplicationResponse
from app.exceptions import NotFoundError, DuplicateNameError

BASE = "/api/v1/applications"


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_create_application(client):
    mock_response = ApplicationResponse(id="01ID", name="my-app", comments=None)
    with patch("app.applications.router.service.create_application", return_value=mock_response):
        resp = await client.post(BASE, json={"name": "my-app"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "my-app"


async def test_create_application_duplicate_returns_409(client):
    with patch(
        "app.applications.router.service.create_application",
        side_effect=DuplicateNameError("Application", "my-app"),
    ):
        resp = await client.post(BASE, json={"name": "my-app"})
    assert resp.status_code == 409


async def test_get_application(client):
    mock_response = ApplicationResponse(id="01ID", name="my-app", comments=None)
    with patch("app.applications.router.service.get_application", return_value=mock_response):
        resp = await client.get(f"{BASE}/01ID")
    assert resp.status_code == 200
    assert resp.json()["id"] == "01ID"


async def test_get_application_not_found(client):
    with patch(
        "app.applications.router.service.get_application",
        side_effect=NotFoundError("Application", "bad-id"),
    ):
        resp = await client.get(f"{BASE}/bad-id")
    assert resp.status_code == 404


async def test_list_applications(client):
    mock_list = [
        ApplicationResponse(id="01A", name="app-a", comments=None),
        ApplicationResponse(id="01B", name="app-b", comments="note"),
    ]
    with patch("app.applications.router.service.list_applications", return_value=mock_list):
        resp = await client.get(BASE)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_update_application(client):
    mock_response = ApplicationResponse(id="01ID", name="renamed", comments=None)
    with patch("app.applications.router.service.update_application", return_value=mock_response):
        resp = await client.put(f"{BASE}/01ID", json={"name": "renamed"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "renamed"
