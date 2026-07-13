from dataclasses import dataclass

from backend.config import Settings


HEADER_NAME = "x-ai-api-key"


@dataclass(frozen=True)
class ApiKeyChoice:
    key: str
    source: str
    used_user_key: bool


def mask_api_key(api_key: str | None) -> str:
    if not api_key:
        return ""

    key = api_key.strip()
    if len(key) <= 8:
        return "*" * len(key)

    return f"{key[:3]}****{key[-4:]}"


def is_reasonable_api_key(api_key: str | None) -> bool:
    if not api_key:
        return False

    key = api_key.strip()
    if len(key) < 12:
        return False
    if any(char.isspace() for char in key):
        return False
    return True


def choose_api_key(user_api_key: str | None, settings: Settings) -> ApiKeyChoice | None:
    cleaned_user_key = (user_api_key or "").strip()
    if cleaned_user_key and settings.allow_user_api_key:
        if not is_reasonable_api_key(cleaned_user_key):
            raise ValueError("用户 API Key 格式不正确，请检查后重新输入。")
        return ApiKeyChoice(key=cleaned_user_key, source="user", used_user_key=True)

    default_key = settings.default_ai_api_key.strip()
    if default_key:
        return ApiKeyChoice(key=default_key, source="default", used_user_key=False)

    return None


def build_key_check_result(user_api_key: str | None, settings: Settings) -> dict:
    cleaned_user_key = (user_api_key or "").strip()
    user_key_valid = is_reasonable_api_key(cleaned_user_key)
    default_configured = bool(settings.default_ai_api_key.strip())

    if cleaned_user_key and settings.allow_user_api_key and user_key_valid:
        active_source = "user"
    elif default_configured:
        active_source = "default"
    else:
        active_source = "none"

    return {
        "allowUserApiKey": settings.allow_user_api_key,
        "hasUserKey": bool(cleaned_user_key),
        "userKeyValid": user_key_valid if cleaned_user_key else None,
        "maskedUserKey": mask_api_key(cleaned_user_key),
        "defaultKeyConfigured": default_configured,
        "activeSource": active_source,
    }

