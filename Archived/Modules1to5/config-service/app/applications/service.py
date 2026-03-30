"""
app/applications/service.py
---------------------------
Business logic for the Applications domain.
Orchestrates repository calls and enforces domain rules.
"""

from app.database import get_connection
from app.applications.models import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from app.applications.repository import ApplicationRepository

_repo = ApplicationRepository()


def create_application(data: ApplicationCreate) -> ApplicationResponse:
    with get_connection() as conn:
        result = _repo.create(conn, name=data.name, comments=data.comments)
    return ApplicationResponse(**result)


def update_application(id: str, data: ApplicationUpdate) -> ApplicationResponse:
    with get_connection() as conn:
        result = _repo.update(conn, id=id, name=data.name, comments=data.comments)
    return ApplicationResponse(**result)


def get_application(id: str) -> ApplicationResponse:
    with get_connection() as conn:
        result = _repo.get_by_id(conn, id=id)
    return ApplicationResponse(**result)


def list_applications() -> list[ApplicationResponse]:
    with get_connection() as conn:
        results = _repo.list_all(conn)
    return [ApplicationResponse(**r) for r in results]
