import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from backend.config import Settings
from backend.services.prompt_service import SYSTEM_PROMPT


class AiServiceError(RuntimeError):
    """Raised when the upstream AI service cannot produce a usable response."""


def call_ai_api(prompt: str, api_key: str, settings: Settings) -> str:
    payload = {
        "model": settings.ai_model,
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }

    request = Request(
        settings.ai_api_base_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.ai_timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        message = exc.read().decode("utf-8", errors="ignore")[:300]
        raise AiServiceError(f"AI 服务返回错误：HTTP {exc.code} {message}") from exc
    except URLError as exc:
        raise AiServiceError("无法连接 AI 服务，请检查网络或 API 地址。") from exc
    except TimeoutError as exc:
        raise AiServiceError("AI 服务响应超时，请稍后重试。") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AiServiceError("AI 服务返回了无法解析的内容。") from exc

    content = _extract_content(payload)
    if not content:
        raise AiServiceError("AI 服务没有返回推荐内容。")
    return content


def _extract_content(payload: dict) -> str:
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content

    output_text = payload.get("output_text")
    if isinstance(output_text, str):
        return output_text

    return ""

