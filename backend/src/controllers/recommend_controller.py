from fastapi import HTTPException

from backend.src.config.settings import get_settings
from backend.src.models.schemas import RecommendRequest, RecommendResponse
from backend.src.services.history_service import HistoryService
from backend.src.services.recommend_service import generate_recommendations


def recommend(
    payload: RecommendRequest,
    user_api_key: str | None,
) -> RecommendResponse:
    try:
        response = generate_recommendations(payload, user_api_key, get_settings())
        HistoryService().record(payload.preferences, response.data)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
