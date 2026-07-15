"""Compatibility export for the member-five pre-refactor route module."""

from backend.src.routes.recommend_routes import router as recommend_router

# Older integration notes referred to this symbol as ``recommend_bp``.
recommend_bp = recommend_router

__all__ = ["recommend_bp", "recommend_router"]
