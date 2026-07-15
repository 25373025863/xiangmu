from fastapi import APIRouter

from backend.src.config.settings import get_settings
from backend.src.services.config_service import get_config_status
from backend.src.utils.response import success

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/check")
def check_config() -> dict:
    return success(get_config_status(get_settings()))
