import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from backend.src.services.key_service import AiProviderConfig
from backend.src.services.prompt_service import SYSTEM_PROMPT


class AiServiceError(RuntimeError):
    """Raised when the upstream AI service cannot produce a usable response."""


def call_ai_api(
    prompt: str,
    provider: AiProviderConfig,
    timeout_seconds: int,
) -> str:
    payload = {
        "model": provider.model,
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    request = Request(
        provider.api_base_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raise AiServiceError(f"AI 服务返回错误：HTTP {exc.code}") from exc
    except URLError as exc:
        raise AiServiceError("无法连接 AI 服务，请检查网络或 API 地址。") from exc
    except TimeoutError as exc:
        raise AiServiceError("AI 服务响应超时，请稍后重试。") from exc

    try:
        response_payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AiServiceError("AI 服务返回了无法解析的内容。") from exc

    choices = response_payload.get("choices")
    if isinstance(choices, list) and choices:
        content = (choices[0].get("message") or {}).get("content")
        if isinstance(content, str) and content:
            return content
    output_text = response_payload.get("output_text")
    if isinstance(output_text, str) and output_text:
        return output_text
    raise AiServiceError("AI 服务没有返回推荐内容。")
