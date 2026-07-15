from fastapi import APIRouter, HTTPException

from backend.src.models.schemas import PreferenceInput
from backend.src.utils.response import success

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


@router.post("/submit")
def submit_preferences(payload: PreferenceInput) -> dict:
    if not payload.genres and not payload.platforms:
        raise HTTPException(status_code=422, detail="游戏类型和平台至少填写一项")
    return success(
        payload.model_dump(mode="json", exclude_none=True),
        "偏好接收成功，已整理为推荐输入。",
    )
