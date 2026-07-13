from fastapi import APIRouter
from src.utils.response import success_response
import time

router = APIRouter()
_start_time = time.time()

@router.get("")
async def health_check():
    return success_response(data={"status": "ok", "uptime": int(time.time() - _start_time)})