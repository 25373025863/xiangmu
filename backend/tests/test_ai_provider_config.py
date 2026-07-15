import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.src.app import app
from backend.src.config.settings import get_settings
from backend.src.models.schemas import GameCandidate, RecommendRequest
from backend.src.services.ai_service import call_ai_api
from backend.src.services.key_service import (
    AiProviderConfig,
    choose_provider_config,
    normalize_api_base_url,
    validate_ai_model,
)
from backend.src.services.recommend_service import generate_recommendations


def _make_settings(**changes):
    defaults = {
        "default_ai_api_key": "",
        "allow_user_api_key": True,
        "ai_api_base_url": "https://api.openai.com/v1/chat/completions",
        "ai_model": "gpt-4o-mini",
    }
    defaults.update(changes)
    return replace(get_settings(), **defaults)


class _FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(
            {"choices": [{"message": {"content": "provider response"}}]}
        ).encode("utf-8")


class AiProviderConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_key_check_prefers_header_and_does_not_persist_raw_keys(self) -> None:
        header_key = "sk-header-secret-1234"
        body_key = "sk-body-secret-5678"
        with tempfile.TemporaryDirectory() as directory:
            settings = _make_settings(data_dir=Path(directory))
            with patch("backend.src.routes.key_routes.get_settings", return_value=settings):
                response = self.client.post(
                    "/api/key/check",
                    headers={"x-ai-api-key": header_key},
                    json={
                        "apiKey": body_key,
                        "apiBaseUrl": "https://gateway.example/v1",
                        "model": "provider-model-v2",
                    },
                )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["data"]["maskedUserKey"], "sk-****1234")
            self.assertEqual(
                payload["data"]["apiBaseUrl"],
                "https://gateway.example/v1/chat/completions",
            )
            self.assertEqual(payload["data"]["model"], "provider-model-v2")
            serialized = response.text
            self.assertNotIn(header_key, serialized)
            self.assertNotIn(body_key, serialized)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_key_check_keeps_legacy_body_key_compatibility(self) -> None:
        body_key = "sk-legacy-secret-4321"
        settings = _make_settings()
        with patch("backend.src.routes.key_routes.get_settings", return_value=settings):
            response = self.client.post(
                "/api/key/check",
                json={"api_key": body_key},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["maskedUserKey"], "sk-****4321")
        self.assertNotIn(body_key, response.text)

    def test_url_normalization_and_local_http_rules(self) -> None:
        self.assertEqual(
            normalize_api_base_url("https://api.example.com/v1"),
            "https://api.example.com/v1/chat/completions",
        )
        self.assertEqual(
            normalize_api_base_url("http://localhost:11434/v1/"),
            "http://localhost:11434/v1/chat/completions",
        )
        self.assertEqual(
            normalize_api_base_url("http://127.0.0.1:8001/chat/completions"),
            "http://127.0.0.1:8001/chat/completions",
        )
        self.assertEqual(
            normalize_api_base_url("http://[::1]:8001/v1"),
            "http://[::1]:8001/v1/chat/completions",
        )

        rejected = (
            "http://api.example.com/v1",
            "https://user:password@api.example.com/v1",
            "https://api.example.com/v1#secret",
            "ftp://api.example.com/v1",
        )
        for endpoint in rejected:
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                normalize_api_base_url(endpoint)

    def test_model_validation(self) -> None:
        self.assertEqual(validate_ai_model("provider/model-v1"), "provider/model-v1")
        for model in ("", "model with spaces", "x" * 201):
            with self.subTest(model=model), self.assertRaises(ValueError):
                validate_ai_model(model)

    def test_default_key_cannot_be_sent_to_a_custom_provider(self) -> None:
        settings = _make_settings(default_ai_api_key="sk-server-secret-1234")
        with self.assertRaisesRegex(ValueError, "有效的用户 API Key"):
            choose_provider_config(
                None,
                settings,
                api_base_url="https://untrusted.example/v1",
            )
        with self.assertRaisesRegex(ValueError, "有效的用户 API Key"):
            choose_provider_config(None, settings, model="custom-model")

        provider = choose_provider_config(
            None,
            settings,
            api_base_url="",
            model="   ",
        )
        self.assertIsNotNone(provider)
        self.assertEqual(provider.api_base_url, settings.ai_api_base_url)
        self.assertEqual(provider.model, settings.ai_model)

    def test_disallowed_user_key_is_rejected_explicitly(self) -> None:
        raw_key = "sk-user-secret-1234"
        settings = _make_settings(
            allow_user_api_key=False,
            default_ai_api_key="sk-server-secret-5678",
        )
        with patch("backend.src.routes.key_routes.get_settings", return_value=settings):
            response = self.client.post(
                "/api/key/check",
                headers={"x-ai-api-key": raw_key},
                json={},
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("不允许使用用户 API Key", response.json()["detail"])
        self.assertNotIn(raw_key, response.text)

    def test_ai_service_uses_provider_url_model_and_hidden_key(self) -> None:
        raw_key = "sk-provider-secret-1234"
        provider = AiProviderConfig(
            api_key=raw_key,
            api_base_url="https://gateway.example/v1/chat/completions",
            model="provider-model-v3",
            source="user",
            used_user_key=True,
        )
        self.assertNotIn(raw_key, repr(provider))

        with patch(
            "backend.src.services.ai_service.urlopen",
            return_value=_FakeResponse(),
        ) as mocked_urlopen:
            content = call_ai_api("prompt", provider, 17)

        self.assertEqual(content, "provider response")
        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, provider.api_base_url)
        self.assertEqual(request.get_header("Authorization"), f"Bearer {raw_key}")
        self.assertEqual(mocked_urlopen.call_args.kwargs["timeout"], 17)
        request_payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request_payload["model"], "provider-model-v3")

    def test_recommendation_uses_request_provider_and_reports_actual_model(self) -> None:
        request = RecommendRequest.model_validate(
            {
                "preferences": {"genres": ["动作"], "platforms": ["PC"]},
                "candidate_games": [
                    GameCandidate(
                        id="test-game",
                        title="测试游戏",
                        genres=["动作"],
                        platforms=["PC"],
                    ).model_dump()
                ],
                "apiBaseUrl": "https://gateway.example/v1",
                "model": "provider-model-v4",
            }
        )
        ai_result = json.dumps(
            {
                "recommendations": [
                    {
                        "title": "测试游戏",
                        "reason": "匹配偏好",
                        "suitable_for": "动作玩家",
                        "match_score": 90,
                    }
                ]
            },
            ensure_ascii=False,
        )
        with patch(
            "backend.src.services.recommend_service.call_ai_api",
            return_value=ai_result,
        ) as mocked_call:
            response = generate_recommendations(
                request,
                "sk-user-secret-7890",
                _make_settings(),
            )

        provider = mocked_call.call_args.args[1]
        self.assertEqual(
            provider.api_base_url,
            "https://gateway.example/v1/chat/completions",
        )
        self.assertEqual(provider.model, "provider-model-v4")
        self.assertEqual(response.meta.model, "provider-model-v4")
        self.assertTrue(response.meta.used_user_key)

    def test_recommend_route_never_writes_raw_key_to_history(self) -> None:
        raw_key = "sk-route-secret-2468"
        ai_result = json.dumps(
            {
                "recommendations": [
                    {
                        "title": "路由测试游戏",
                        "reason": "匹配偏好",
                        "suitable_for": "测试玩家",
                        "match_score": 88,
                    }
                ]
            },
            ensure_ascii=False,
        )
        with tempfile.TemporaryDirectory() as directory:
            settings = _make_settings(data_dir=Path(directory))
            with (
                patch(
                    "backend.src.controllers.recommend_controller.get_settings",
                    return_value=settings,
                ),
                patch(
                    "backend.src.services.history_service.get_settings",
                    return_value=settings,
                ),
                patch(
                    "backend.src.services.recommend_service.call_ai_api",
                    return_value=ai_result,
                ) as mocked_call,
            ):
                response = self.client.post(
                    "/api/recommend",
                    headers={"x-ai-api-key": raw_key},
                    json={
                        "preferences": {"genres": ["动作"], "platforms": ["PC"]},
                        "candidate_games": [
                            {
                                "id": "route-test",
                                "title": "路由测试游戏",
                                "genres": ["动作"],
                                "platforms": ["PC"],
                            }
                        ],
                        "apiBaseUrl": "https://route.example/v1",
                        "model": "route-model",
                    },
                )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["meta"]["model"], "route-model")
            provider = mocked_call.call_args.args[1]
            self.assertEqual(
                provider.api_base_url,
                "https://route.example/v1/chat/completions",
            )
            history_text = (Path(directory) / "histories.json").read_text(
                encoding="utf-8"
            )
            self.assertNotIn(raw_key, response.text)
            self.assertNotIn(raw_key, history_text)

    def test_config_check_returns_default_provider_settings(self) -> None:
        settings = _make_settings(
            ai_api_base_url="https://default.example/v1",
            ai_model="default-model",
        )
        with patch("backend.src.routes.config_routes.get_settings", return_value=settings):
            response = self.client.get("/api/config/check")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(
            data["apiBaseUrl"],
            "https://default.example/v1/chat/completions",
        )
        self.assertEqual(data["model"], "default-model")


if __name__ == "__main__":
    unittest.main()
