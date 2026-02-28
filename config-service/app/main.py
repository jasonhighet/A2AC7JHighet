"""
app/main.py
-----------
FastAPI application factory.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import DuplicateNameError, NotFoundError
from app.applications.router import router as applications_router
from app.configurations.router import router as configurations_router

app = FastAPI(
    title="Config Service",
    description="Centralized configuration management REST API",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(DuplicateNameError)
async def duplicate_handler(request: Request, exc: DuplicateNameError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(applications_router, prefix="/api/v1")
app.include_router(configurations_router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}
