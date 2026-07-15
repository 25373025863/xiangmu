"""Compatibility adapter for the member-five pre-refactor service module."""

from backend.src.config.settings import get_settings
from backend.src.models.schemas import RecommendRequest
from backend.src.services.recommend_service import generate_recommendations as _generate


def generate_recommendations(preferences: dict) -> list[dict]:
    request = RecommendRequest(preferences=preferences)
    response = _generate(request, None, get_settings())
    return [item.model_dump(mode="json") for item in response.data]
