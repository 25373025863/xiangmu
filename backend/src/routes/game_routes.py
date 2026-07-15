from fastapi import APIRouter, Query

from backend.src.controllers.game_controller import get_game, list_games

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("")
def games(
    keyword: str = Query(default="", max_length=100),
    genre: str = Query(default="", max_length=50),
    platform: str = Query(default="", max_length=50),
    tag: str = Query(default="", max_length=50),
) -> dict:
    return list_games(keyword, genre, platform, tag)


@router.get("/{game_id}")
def game_detail(game_id: str) -> dict:
    return get_game(game_id)
