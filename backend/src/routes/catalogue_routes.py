from typing import Literal

from fastapi import APIRouter, Query

from backend.src.services.catalogue_service import catalogue_service
from backend.src.utils.response import success


router = APIRouter(prefix="/api/catalogue", tags=["catalogue"])


@router.get("/games")
def catalogue_games(
    keyword: str = Query(default="", max_length=100),
    sort: Literal["topsellers", "released", "price", "name"] = "topsellers",
    page: int = Query(default=1, ge=1),
    size: int = Query(default=12, ge=1, le=25),
) -> dict:
    data = catalogue_service.list_games(
        keyword=keyword,
        sort=sort,
        page=page,
        size=size,
    )
    message = data.get("fallback_message", "success")
    return success(data, message)
