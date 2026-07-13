import json
from pathlib import Path
from datetime import datetime
from src.config.settings import settings

async def get_config_status():
    status = {
        "status": "ok",
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

    ai_configured = settings.is_ai_configured
    status["ai_configured"] = ai_configured

    games_file = settings.DATA_DIR / "games.json"
    if games_file.exists():
        try:
            with open(games_file, 'r', encoding='utf-8') as f:
                games = json.load(f)
                status["games_count"] = len(games) if isinstance(games, list) else 0
                status["games_data_exists"] = True
        except:
            status["games_data_exists"] = False
            status["games_count"] = 0
    else:
        status["games_data_exists"] = False
        status["games_count"] = 0

    status["allow_user_api_key"] = settings.ALLOW_USER_API_KEY
    status["environment"] = "production" if not settings.DEBUG else "development"

    if not ai_configured:
        status["message"] = "AI 服务未配置"
        status["status"] = "warning"
    else:
        status["message"] = "系统运行正常"

    return status