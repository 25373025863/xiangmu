import json
import os
import tempfile
from pathlib import Path
from threading import RLock
from typing import Any


class JsonListStore:
    """Small local JSON store with atomic replacement for one-process development use."""

    _lock = RLock()

    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path

    def read(self) -> list[dict[str, Any]]:
        with self._lock:
            if not self._file_path.exists():
                return []
            records = json.loads(self._file_path.read_text(encoding="utf-8"))
            if not isinstance(records, list):
                raise ValueError(f"{self._file_path.name} 顶层必须是数组")
            return [record for record in records if isinstance(record, dict)]

    def write(self, records: list[dict[str, Any]]) -> None:
        with self._lock:
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temp_name = tempfile.mkstemp(
                prefix=f".{self._file_path.stem}-",
                suffix=".json",
                dir=self._file_path.parent,
            )
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as target:
                    json.dump(records, target, ensure_ascii=False, indent=2)
                    target.write("\n")
                Path(temp_name).replace(self._file_path)
            finally:
                if os.path.exists(temp_name):
                    os.unlink(temp_name)
