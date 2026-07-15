from fastapi import APIRouter, Header

from backend.src.controllers.recommend_controller import recommend
from backend.src.models.schemas import RecommendRequest, RecommendResponse

router = APIRouter(prefix="/api/recommend", tags=["recommend"])


@router.post("", response_model=RecommendResponse)
def create_recommendations(
    payload: RecommendRequest,
    user_api_key: str | None = Header(default=None, alias="x-ai-api-key"),
) -> RecommendResponse:
    return recommend(payload, user_api_key)
