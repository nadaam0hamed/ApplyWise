from fastapi import APIRouter

from app.schemas.health import HealthResponse, RootResponse
from app.utils.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    return RootResponse(
        message=f"Welcome to {settings.app_name}",
        docs_url="/docs",
        health_url="/health",
    )


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.app_env,
    )
