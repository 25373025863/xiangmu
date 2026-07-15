from datetime import UTC, datetime

from backend.src.config.settings import get_settings
from backend.src.repositories.json_list_store import JsonListStore
from backend.src.services.game_service import GameService


class FavoriteNotFoundError(LookupError):
    """Raised when a favorite cannot be found."""


class FavoriteService:
    def __init__(self) -> None:
        self._store = JsonListStore(get_settings().data_dir / "favorites.json")
        self._games = GameService()

    def list(self, page: int, size: int) -> tuple[list[dict], int]:
        records = sorted(
            self._store.read(),
            key=lambda record: str(record.get("favorited_at", "")),
            reverse=True,
        )
        return _paginate(records, page, size)

    def add(self, game_id: str) -> tuple[dict, bool]:
        game = self._games.get_game(game_id)
        if game is None:
            raise FavoriteNotFoundError(game_id)
        records = self._store.read()
        for record in records:
            if record.get("id") == game["id"]:
                return record, False
        record = {
            **game,
            "favorited_at": datetime.now(UTC).isoformat(),
        }
        records.append(record)
        self._store.write(records)
        return record, True

    def delete(self, game_id: str) -> None:
        records = self._store.read()
        remaining = [record for record in records if record.get("id") != game_id]
        if len(remaining) == len(records):
            raise FavoriteNotFoundError(game_id)
        self._store.write(remaining)


def _paginate(records: list[dict], page: int, size: int) -> tuple[list[dict], int]:
    start = (page - 1) * size
    return records[start : start + size], len(records)
