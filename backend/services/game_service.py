"""Game detail queries built on the shared catalogue data."""

import json
from pathlib import Path
from typing import Any

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "games.json"

# These fields are presentation details. They can move into games.json once the
# game-data module owns complete records, without changing the API contract.
DETAIL_METADATA: dict[str, dict[str, Any]] = {
    "g001": {
        "cover": "https://cdn.akamai.steamstatic.com/steam/apps/413150/header.jpg",
        "developer": "ConcernedApe",
        "release_date": "2016-02-26",
        "suitable_for": ["喜欢轻松经营和长期养成的玩家", "想和朋友低压力合作游玩的玩家"],
        "purchase_url": "https://store.steampowered.com/app/413150/Stardew_Valley/",
    },
    "g002": {
        "cover": "https://cdn.akamai.steamstatic.com/steam/apps/1426210/header.jpg",
        "developer": "Hazelight Studios",
        "release_date": "2021-03-26",
        "suitable_for": ["有固定搭档的双人玩家", "喜欢关卡创意和合作沟通的玩家"],
        "purchase_url": "https://store.steampowered.com/app/1426210/It_Takes_Two/",
    },
    "g003": {
        "cover": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg",
        "developer": "Supergiant Games",
        "release_date": "2020-09-17",
        "suitable_for": ["喜欢快节奏动作战斗的玩家", "愿意反复挑战并逐步解锁剧情的玩家"],
        "purchase_url": "https://store.steampowered.com/app/1145360/Hades/",
    },
    "g004": {
        "developer": "Nintendo EPD",
        "release_date": "2017-03-03",
        "suitable_for": ["喜欢开放世界探索和解谜的玩家", "享受自由尝试与发现的单人玩家"],
        "purchase_url": "https://www.nintendo.com/us/store/products/the-legend-of-zelda-breath-of-the-wild-switch/",
    },
    "g005": {
        "cover": "https://cdn.akamai.steamstatic.com/steam/apps/289070/header.jpg",
        "developer": "Firaxis Games",
        "release_date": "2016-10-21",
        "suitable_for": ["喜欢回合策略和长期规划的玩家", "愿意投入较长单局时间的玩家"],
        "purchase_url": "https://store.steampowered.com/app/289070/Sid_Meiers_Civilization_VI/",
    },
}


class GameDataError(Exception):
    """Raised when the local game catalogue cannot be loaded."""


class GameNotFoundError(Exception):
    """Raised when a game ID is not in the catalogue."""


def get_game_detail(game_id: str) -> dict[str, Any]:
    normalized_id = game_id.strip().casefold()
    for game in _load_games():
        stored_id = game.get("id")
        if isinstance(stored_id, str) and stored_id.casefold() == normalized_id:
            metadata = DETAIL_METADATA.get(stored_id, {})
            return {
                "id": stored_id,
                "title": game.get("title", "未命名游戏"),
                "cover": metadata.get("cover"),
                "genres": game.get("genres", []),
                "platforms": game.get("platforms", []),
                "tags": game.get("tags", []),
                "price": game.get("price"),
                "score": game.get("score"),
                "developer": metadata.get("developer"),
                "release_date": metadata.get("release_date"),
                "description": game.get("description", ""),
                "suitable_for": metadata.get("suitable_for", []),
                "purchase_url": metadata.get("purchase_url"),
            }
    raise GameNotFoundError(game_id)


def _load_games() -> list[dict[str, Any]]:
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GameDataError from exc

    if not isinstance(data, list) or any(not isinstance(game, dict) for game in data):
        raise GameDataError
    return data
