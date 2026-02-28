"""
app/applications/models.py
--------------------------
Pydantic request/response models for the Applications domain.
"""

from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    name: str
    comments: str | None = None


class ApplicationUpdate(BaseModel):
    name: str | None = None
    comments: str | None = None


class ApplicationResponse(BaseModel):
    id: str
    name: str
    comments: str | None = None
