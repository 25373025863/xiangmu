from fastapi import APIRouter, Query

from backend.src.services.history_service import HistoryService
from backend.src.utils.response import success

router = APIRouter(prefix="/api/histories", tags=["histories"])


@router.get("")
def list_histories(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
) -> dict:
    items, total = HistoryService().list(page, size)
    return success({"list": items, "total": total, "page": page, "size": size})
