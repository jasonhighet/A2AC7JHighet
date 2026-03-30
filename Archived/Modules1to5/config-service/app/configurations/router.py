"""
app/configurations/router.py
-----------------------------
FastAPI routes for the Configurations resource.
All routes are mounted under /api/v1/configurations by main.py.
"""

from fastapi import APIRouter

from app.configurations.models import (
    ConfigurationCreate,
    ConfigurationResponse,
    ConfigurationUpdate,
)
from app.configurations import service

router = APIRouter(prefix="/configurations", tags=["configurations"])


@router.post("", response_model=ConfigurationResponse, status_code=201)
async def create_configuration(body: ConfigurationCreate) -> ConfigurationResponse:
    return service.create_configuration(body)


@router.put("/{id}", response_model=ConfigurationResponse)
async def update_configuration(id: str, body: ConfigurationUpdate) -> ConfigurationResponse:
    return service.update_configuration(id, body)


@router.get("/{id}", response_model=ConfigurationResponse)
async def get_configuration(id: str) -> ConfigurationResponse:
    return service.get_configuration(id)
