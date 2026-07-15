import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    debug: bool
    port: int
    default_ai_api_key: str
    allow_user_api_key: bool
    ai_api_base_url: str
    ai_model: str
    ai_timeout_seconds: int
    demo_mode_without_key: bool
    data_dir: Path
    frontend_dir: Path


@lru_cache
def get_settings() -> Settings:
    if load_dotenv:
        load_dotenv()

    project_root = Path(__file__).resolve().parents[3]
    timeout_raw = os.getenv("AI_TIMEOUT_SECONDS", "30").strip()
    port_raw = os.getenv("PORT", "8000").strip()
    try:
        timeout = max(5, int(timeout_raw))
    except ValueError:
        timeout = 30
    try:
        port = int(port_raw)
    except ValueError:
        port = 8000

    return Settings(
        app_name=os.getenv("APP_NAME", "AI Game Recommendation API"),
        app_version=os.getenv("APP_VERSION", "1.0.0"),
        debug=_parse_bool(os.getenv("DEBUG"), False),
        port=port,
        default_ai_api_key=os.getenv("DEFAULT_AI_API_KEY", "").strip(),
        allow_user_api_key=_parse_bool(os.getenv("ALLOW_USER_API_KEY"), True),
        ai_api_base_url=os.getenv(
            "AI_API_BASE_URL", "https://api.openai.com/v1/chat/completions"
        ).strip(),
        ai_model=os.getenv("AI_MODEL", "gpt-4o-mini").strip(),
        ai_timeout_seconds=timeout,
        demo_mode_without_key=_parse_bool(os.getenv("DEMO_MODE_WITHOUT_KEY"), True),
        data_dir=project_root / "backend" / "src" / "data",
        frontend_dir=project_root / "frontend",
    )
