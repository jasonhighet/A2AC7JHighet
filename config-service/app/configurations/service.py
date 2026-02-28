"""
app/configurations/service.py
------------------------------
Business logic for the Configurations domain.
"""

from app.database import get_connection
from app.configurations.models import (
    ConfigurationCreate,
    ConfigurationUpdate,
    ConfigurationResponse,
)
from app.configurations.repository import ConfigurationRepository

_repo = ConfigurationRepository()


def create_configuration(data: ConfigurationCreate) -> ConfigurationResponse:
    with get_connection() as conn:
        result = _repo.create(
            conn,
            application_id=data.application_id,
            name=data.name,
            comments=data.comments,
            config=data.config,
        )
    return ConfigurationResponse(**result)


def update_configuration(id: str, data: ConfigurationUpdate) -> ConfigurationResponse:
    with get_connection() as conn:
        result = _repo.update(
            conn,
            id=id,
            name=data.name,
            comments=data.comments,
            config=data.config,
        )
    return ConfigurationResponse(**result)


def get_configuration(id: str) -> ConfigurationResponse:
    with get_connection() as conn:
        result = _repo.get_by_id(conn, id=id)
    return ConfigurationResponse(**result)
