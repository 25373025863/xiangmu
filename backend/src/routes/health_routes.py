from fastapi import APIRouter

from backend.src.config.settings import get_settings
from backend.src.utils.response import success

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def health() -> dict:
    settings = get_settings()
    return success(
        {"status": "ok", "version": settings.app_version},
        "backend is running",
    )
