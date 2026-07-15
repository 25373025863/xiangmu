from fastapi import APIRouter, Header, HTTPException

from backend.src.config.settings import get_settings
from backend.src.models.schemas import KeyCheckRequest, KeyCheckResponse
from backend.src.services.key_service import HEADER_NAME, build_key_check_result

router = APIRouter(prefix="/api/key", tags=["api-key"])


@router.post("/check", response_model=KeyCheckResponse)
def check_key(
    payload: KeyCheckRequest,
    header_api_key: str | None = Header(default=None, alias=HEADER_NAME),
) -> KeyCheckResponse:
    user_api_key = (
        header_api_key
        if header_api_key and header_api_key.strip()
        else payload.api_key
    )
    try:
        data = build_key_check_result(
            user_api_key,
            get_settings(),
            api_base_url=payload.api_base_url,
            model=payload.model,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return KeyCheckResponse(data=data)
