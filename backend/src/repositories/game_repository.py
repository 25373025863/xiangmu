import json
from pathlib import Path

from backend.src.config.settings import get_settings


class GameRepository:
    def __init__(self, data_path: Path | None = None) -> None:
        self._data_path = data_path or get_settings().data_dir / "games.json"

    def get_all(self) -> list[dict]:
        with self._data_path.open("r", encoding="utf-8") as source:
            records = json.load(source)
        if not isinstance(records, list):
            raise ValueError("games.json 顶层必须是数组")
        return records

    def get_by_id(self, game_id: str) -> dict | None:
        normalized_id = game_id.strip().casefold()
        return next(
            (
                game
                for game in self.get_all()
                if str(game.get("id", "")).casefold() == normalized_id
            ),
            None,
        )
