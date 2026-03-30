"""
app/applications/router.py
--------------------------
FastAPI routes for the Applications resource.
All routes are mounted under /api/v1/applications by main.py.
"""

from fastapi import APIRouter

from app.applications.models import ApplicationCreate, ApplicationResponse, ApplicationUpdate
from app.applications import service

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationResponse, status_code=201)
async def create_application(body: ApplicationCreate) -> ApplicationResponse:
    return service.create_application(body)


@router.put("/{id}", response_model=ApplicationResponse)
async def update_application(id: str, body: ApplicationUpdate) -> ApplicationResponse:
    return service.update_application(id, body)


@router.get("/{id}", response_model=ApplicationResponse)
async def get_application(id: str) -> ApplicationResponse:
    return service.get_application(id)


@router.get("", response_model=list[ApplicationResponse])
async def list_applications() -> list[ApplicationResponse]:
    return service.list_applications()
