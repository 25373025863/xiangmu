from fastapi import HTTPException

from backend.src.services.game_service import GameService
from backend.src.utils.response import success


def list_games(keyword: str, genre: str, platform: str, tag: str) -> dict:
    games = GameService().list_games(keyword, genre, platform, tag)
    return success({"items": games, "total": len(games)})


def get_game(game_id: str) -> dict:
    game = GameService().get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="游戏不存在")
    return success(game)
