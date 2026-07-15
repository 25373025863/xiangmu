from datetime import UTC, datetime
from uuid import uuid4

from backend.src.config.settings import get_settings
from backend.src.models.schemas import PreferenceInput, RecommendationItem
from backend.src.repositories.json_list_store import JsonListStore


class HistoryService:
    def __init__(self) -> None:
        self._store = JsonListStore(get_settings().data_dir / "histories.json")

    def record(
        self,
        preferences: PreferenceInput,
        recommendations: list[RecommendationItem],
    ) -> dict:
        records = self._store.read()
        record = {
            "id": uuid4().hex,
            "created_at": datetime.now(UTC).isoformat(),
            "preferences": preferences.model_dump(mode="json", exclude_none=True),
            "recommendations": [item.model_dump(mode="json") for item in recommendations],
        }
        records.append(record)
        self._store.write(records)
        return record

    def list(self, page: int, size: int) -> tuple[list[dict], int]:
        records = sorted(
            self._store.read(),
            key=lambda record: str(record.get("created_at", "")),
            reverse=True,
        )
        start = (page - 1) * size
        return records[start : start + size], len(records)
