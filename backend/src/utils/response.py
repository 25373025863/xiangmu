from datetime import UTC, datetime
from typing import Any


def success(data: Any = None, message: str = "success", **extra: Any) -> dict[str, Any]:
    payload = {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    payload.update(extra)
    return payload


def failure(message: str, code: str, details: Any = None) -> dict[str, Any]:
    return {
        "success": False,
        "message": message,
        "error": {"code": code, "details": details},
        "timestamp": datetime.now(UTC).isoformat(),
    }
