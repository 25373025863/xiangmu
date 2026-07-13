import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Settings:
    DEFAULT_AI_API_KEY: str = os.getenv("DEFAULT_AI_API_KEY", "")
    ALLOW_USER_API_KEY: bool = os.getenv("ALLOW_USER_API_KEY", "true").lower() == "true"
    APP_NAME: str = "Game Recommend API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    PORT: int = int(os.getenv("PORT", 8000))
    DATA_DIR: Path = Path(__file__).parent.parent / "data"

    @property
    def is_ai_configured(self) -> bool:
        return bool(self.DEFAULT_AI_API_KEY) and len(self.DEFAULT_AI_API_KEY) > 5

settings = Settings()
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)