from fastapi import APIRouter
from src.controllers import config_controller

router = APIRouter()

@router.get("/check")
async def check_config():
    return await config_controller.check_config()