from fastapi import APIRouter, HTTPException, Query, status

from backend.src.models.schemas import FavoriteCreateRequest
from backend.src.services.favorite_service import FavoriteNotFoundError, FavoriteService
from backend.src.utils.response import success

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.get("")
def list_favorites(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
) -> dict:
    items, total = FavoriteService().list(page, size)
    return success({"list": items, "total": total, "page": page, "size": size})


@router.post("", status_code=status.HTTP_201_CREATED)
def add_favorite(payload: FavoriteCreateRequest) -> dict:
    try:
        item, created = FavoriteService().add(payload.game_id)
    except FavoriteNotFoundError as exc:
        raise HTTPException(status_code=404, detail="游戏不存在") from exc
    return success(item, "收藏已保存" if created else "该游戏已收藏", created=created)


@router.delete("/{game_id}")
def delete_favorite(game_id: str) -> dict:
    try:
        FavoriteService().delete(game_id)
    except FavoriteNotFoundError as exc:
        raise HTTPException(status_code=404, detail="收藏不存在") from exc
    return success(None, "收藏已删除")
