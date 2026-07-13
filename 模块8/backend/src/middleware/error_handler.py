from fastapi import Request
from fastapi.responses import JSONResponse
from src.utils.response import error_response

async def error_handler(request: Request, exc: Exception):
    return error_response(message=f"服务器错误: {str(exc)}", status_code=500)