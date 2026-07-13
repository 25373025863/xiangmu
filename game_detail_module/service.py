import json
from pathlib import Path
from typing import Any

DATA_FILE = Path(__file__).resolve().parent / "data" / "games.json"


class GameDataError(Exception):
    """Raised when module-owned game data is not available."""


class GameNotFoundError(Exception):
    """Raised when no game has the requested stable ID."""


def get_game_detail(game_id: str) -> dict[str, Any]:
    normalized_id = game_id.strip().casefold()
    for game in _load_games():
        stored_id = game.get("id")
        if isinstance(stored_id, str) and stored_id.casefold() == normalized_id:
            return game
    raise GameNotFoundError(game_id)


def _load_games() -> list[dict[str, Any]]:
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GameDataError from exc

    if not isinstance(data, list) or any(not isinstance(game, dict) for game in data):
        raise GameDataError
    return data
