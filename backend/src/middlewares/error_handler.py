from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.src.services.ai_service import AiServiceError
from backend.src.utils.response import failure


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=failure("请求参数校验失败", "VALIDATION_ERROR", exc.errors()),
    )


async def ai_error_handler(request: Request, exc: AiServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content=failure(str(exc), "AI_SERVICE_ERROR"),
    )
