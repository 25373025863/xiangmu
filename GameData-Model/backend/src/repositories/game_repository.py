"""JSON data repository. Replace this class when adding SQLite or an API client."""

import json
from pathlib import Path

from backend.src.models.game import Game


class GameRepository:
    def __init__(self, data_path: Path | None = None) -> None:
        backend_root = Path(__file__).resolve().parents[2]
        self._data_path = data_path or backend_root / "data" / "games.json"

    def get_all(self) -> list[Game]:
        with self._data_path.open("r", encoding="utf-8") as source:
            records = json.load(source)
        return [Game.from_dict(record) for record in records]

    def get_by_id(self, game_id: str) -> Game | None:
        return next((game for game in self.get_all() if game.id == game_id), None)
