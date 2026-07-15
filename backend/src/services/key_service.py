from dataclasses import dataclass, field
from urllib.parse import urlsplit, urlunsplit

from backend.src.config.settings import Settings

HEADER_NAME = "x-ai-api-key"


@dataclass(frozen=True)
class ApiKeyChoice:
    key: str
    source: str
    used_user_key: bool


@dataclass(frozen=True)
class AiProviderConfig:
    api_key: str = field(repr=False)
    api_base_url: str
    model: str
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
    return len(key) >= 12 and not any(char.isspace() for char in key)


def normalize_api_base_url(api_base_url: str) -> str:
    cleaned = api_base_url.strip()
    if not cleaned or any(char.isspace() for char in cleaned):
        raise ValueError("AI API 地址不能为空或包含空白字符。")
    try:
        parsed = urlsplit(cleaned)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("AI API 地址格式不正确。") from exc
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not hostname:
        raise ValueError("AI API 地址必须是完整的 HTTP(S) URL。")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("AI API 地址不能包含用户名或密码。")
    if parsed.fragment:
        raise ValueError("AI API 地址不能包含 fragment。")
    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if scheme == "http" and hostname.lower() not in local_hosts:
        raise ValueError("公网 AI API 地址必须使用 HTTPS。")

    path = parsed.path
    if path.rstrip("/").endswith("/v1"):
        path = f"{path.rstrip('/')}/chat/completions"
    return urlunsplit((scheme, parsed.netloc, path, parsed.query, ""))


def validate_ai_model(model: str) -> str:
    cleaned = model.strip()
    if not cleaned:
        raise ValueError("AI 模型不能为空。")
    if len(cleaned) > 200:
        raise ValueError("AI 模型名称不能超过 200 个字符。")
    if any(char.isspace() for char in cleaned):
        raise ValueError("AI 模型名称不能包含空白字符。")
    return cleaned


def _clean_optional_override(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def choose_api_key(user_api_key: str | None, settings: Settings) -> ApiKeyChoice | None:
    cleaned_user_key = (user_api_key or "").strip()
    if cleaned_user_key:
        if not settings.allow_user_api_key:
            raise ValueError("服务器当前不允许使用用户 API Key。")
        if not is_reasonable_api_key(cleaned_user_key):
            raise ValueError("用户 API Key 格式不正确，请检查后重新输入。")
        return ApiKeyChoice(cleaned_user_key, "user", True)
    if settings.default_ai_api_key:
        return ApiKeyChoice(settings.default_ai_api_key, "default", False)
    return None


def choose_provider_config(
    user_api_key: str | None,
    settings: Settings,
    *,
    api_base_url: str | None = None,
    model: str | None = None,
) -> AiProviderConfig | None:
    key_choice = choose_api_key(user_api_key, settings)
    custom_url = _clean_optional_override(api_base_url)
    custom_model = _clean_optional_override(model)
    has_user_override = custom_url is not None or custom_model is not None
    if has_user_override and (key_choice is None or not key_choice.used_user_key):
        raise ValueError("自定义 AI API 地址或模型时必须同时提供有效的用户 API Key。")
    if key_choice is None:
        return None

    effective_url = normalize_api_base_url(
        custom_url if custom_url is not None else settings.ai_api_base_url
    )
    effective_model = validate_ai_model(
        custom_model if custom_model is not None else settings.ai_model
    )
    return AiProviderConfig(
        api_key=key_choice.key,
        api_base_url=effective_url,
        model=effective_model,
        source=key_choice.source,
        used_user_key=key_choice.used_user_key,
    )


def build_key_check_result(
    user_api_key: str | None,
    settings: Settings,
    *,
    api_base_url: str | None = None,
    model: str | None = None,
) -> dict:
    cleaned_user_key = (user_api_key or "").strip()
    if cleaned_user_key and not settings.allow_user_api_key:
        raise ValueError("服务器当前不允许使用用户 API Key。")
    user_key_valid = is_reasonable_api_key(cleaned_user_key)
    default_configured = bool(settings.default_ai_api_key)
    custom_url = _clean_optional_override(api_base_url)
    custom_model = _clean_optional_override(model)
    has_user_override = custom_url is not None or custom_model is not None
    if has_user_override and not user_key_valid:
        raise ValueError("自定义 AI API 地址或模型时必须同时提供有效的用户 API Key。")

    provider = choose_provider_config(
        cleaned_user_key if user_key_valid else None,
        settings,
        api_base_url=custom_url,
        model=custom_model,
    )
    effective_url = (
        provider.api_base_url
        if provider
        else normalize_api_base_url(settings.ai_api_base_url)
    )
    effective_model = (
        provider.model if provider else validate_ai_model(settings.ai_model)
    )
    return {
        "allowUserApiKey": settings.allow_user_api_key,
        "hasUserKey": bool(cleaned_user_key),
        "userKeyValid": user_key_valid if cleaned_user_key else None,
        "maskedUserKey": mask_api_key(cleaned_user_key),
        "defaultKeyConfigured": default_configured,
        "activeSource": provider.source if provider else "none",
        "apiBaseUrl": effective_url,
        "model": effective_model,
    }
