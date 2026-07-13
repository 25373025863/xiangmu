from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import FileResponse

from game_detail_module.models import GameDetailResponse
from game_detail_module.service import GameDataError, GameNotFoundError, get_game_detail

MODULE_DIR = Path(__file__).resolve().parent
DETAIL_PAGE = MODULE_DIR / "frontend" / "game-detail.html"

router = APIRouter(tags=["game-detail"])


@router.get("/games/{game_id}", include_in_schema=False)
def game_detail_page(game_id: str) -> FileResponse:
    return FileResponse(DETAIL_PAGE)


@router.get("/api/games/{game_id}", response_model=GameDetailResponse)
def game_detail(game_id: str) -> GameDetailResponse:
    try:
        return GameDetailResponse(data=get_game_detail(game_id))
    except GameNotFoundError as exc:
        raise HTTPException(status_code=404, detail="游戏不存在") from exc
    except GameDataError as exc:
        raise HTTPException(status_code=500, detail="游戏数据暂时不可用") from exc


def create_app() -> FastAPI:
    app = FastAPI(title="Game Detail Module", version="1.0.0")
    app.include_router(router)
    return app


app = create_app()
