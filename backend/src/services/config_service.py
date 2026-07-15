import json

from backend.src.config.settings import Settings
from backend.src.services.key_service import normalize_api_base_url, validate_ai_model


def get_config_status(settings: Settings) -> dict:
    games_file = settings.data_dir / "games.json"
    games_count = 0
    games_data_exists = False
    if games_file.exists():
        try:
            records = json.loads(games_file.read_text(encoding="utf-8"))
            games_count = len(records) if isinstance(records, list) else 0
            games_data_exists = isinstance(records, list)
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "status": "ok" if games_data_exists else "warning",
        "version": settings.app_version,
        "aiConfigured": bool(settings.default_ai_api_key),
        "allowUserApiKey": settings.allow_user_api_key,
        "apiBaseUrl": normalize_api_base_url(settings.ai_api_base_url),
        "model": validate_ai_model(settings.ai_model),
        "gamesDataExists": games_data_exists,
        "gamesCount": games_count,
        "environment": "development" if settings.debug else "production",
    }
