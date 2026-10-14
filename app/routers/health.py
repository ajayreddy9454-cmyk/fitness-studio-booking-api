"""Health check router to verify API operational status."""

from datetime import datetime, timezone
from fastapi import APIRouter, status
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Schema for health check endpoint response."""

    status: str
    app_name: str
    version: str
    timestamp: str


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Returns the operational status and metadata of the API service.",
    tags=["Health"],
)
def get_health() -> HealthResponse:
    """Check if the API server is up and responsive."""
    return HealthResponse(
        status="healthy",
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
