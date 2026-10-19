"""Health check endpoints."""

from fastapi import APIRouter

from app.config import get_settings
from app.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version="0.1.0",
    )
