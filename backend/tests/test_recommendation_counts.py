import json
import unittest
from dataclasses import replace
from unittest.mock import patch

from backend.src.config.settings import get_settings
from backend.src.models.schemas import GameCandidate, PreferenceInput, RecommendRequest
from backend.src.services.recommend_service import (
    generate_recommendations,
    load_recommendation_candidates,
    parse_ai_recommendations,
)


def make_settings():
    return replace(
        get_settings(),
        default_ai_api_key="",
        allow_user_api_key=True,
        demo_mode_without_key=True,
    )


def candidates(count: int = 5) -> list[GameCandidate]:
    return [
        GameCandidate(
            id=f"candidate-{index}",
            steam_app_id=1000 + index,
            title=f"候选游戏 {index}",
            genres=["动作" if index < 3 else "策略"],
            platforms=["PC"],
            score=10 - index,
            source="steam",
            store_url=f"https://store.steampowered.com/app/{1000 + index}/",
        )
        for index in range(1, count + 1)
    ]


def ai_payload(items: list[dict]) -> str:
    return json.dumps({"recommendations": items}, ensure_ascii=False)


class RecommendationCountTests(unittest.TestCase):
    def test_ai_shortfall_is_backfilled_to_target_count(self) -> None:
        request = RecommendRequest(
            preferences=PreferenceInput(genres=["动作"], platforms=["PC"]),
            candidate_games=candidates(),
            limit=5,
            api_base_url="https://provider.example/v1",
            model="provider-model",
        )
        result = ai_payload(
            [
                {
                    "game_id": "candidate-1",
                    "title": "候选游戏 1",
                    "reason": "最符合动作偏好",
                    "suitable_for": "动作玩家",
                    "match_score": 96,
                }
            ]
        )

        with patch(
            "backend.src.services.recommend_service.call_ai_api",
            return_value=result,
        ) as mocked_call:
            response = generate_recommendations(
                request,
                "sk-user-secret-1234",
                make_settings(),
            )

        self.assertEqual(mocked_call.call_count, 1)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data[0].game_id, "candidate-1")
        self.assertEqual(len({item.game_id for item in response.data}), 5)
        self.assertEqual(response.meta.returned_count, 5)
        self.assertEqual(response.meta.candidate_count, 5)
        self.assertTrue(all(item.store_url for item in response.data))

    def test_invalid_entries_do_not_consume_the_limit(self) -> None:
        items = parse_ai_recommendations(
            ai_payload(
                [
                    None,
                    {},
                    {"title": "第一款"},
                    "invalid",
                    {"title": "第二款"},
                    {"title": "不应进入结果"},
                ]
            ),
            2,
        )

        self.assertEqual([item.title for item in items], ["第一款", "第二款"])

    def test_duplicates_hallucinations_and_owned_games_are_replaced(self) -> None:
        available = candidates()
        preferences = PreferenceInput(
            genres=["动作"],
            platforms=["PC"],
            steam_summary={
                "visibility": "public",
                "game_count": 2,
                "owned_game_app_ids": [1001, 1002],
                "top_games": [],
            },
        )
        request = RecommendRequest(
            preferences=preferences,
            candidate_games=available,
            limit=5,
            api_base_url="https://provider.example/v1",
            model="provider-model",
        )
        result = ai_payload(
            [
                {"game_id": "candidate-1", "title": "候选游戏 1"},
                {"game_id": "candidate-3", "title": "候选游戏 3"},
                {"title": "候选游戏 3"},
                {"title": "模型虚构的游戏"},
            ]
        )

        with patch(
            "backend.src.services.recommend_service.call_ai_api",
            return_value=result,
        ):
            response = generate_recommendations(
                request,
                "sk-user-secret-1234",
                make_settings(),
            )

        self.assertEqual(len(response.data), 3)
        self.assertEqual(
            {item.game_id for item in response.data},
            {"candidate-3", "candidate-4", "candidate-5"},
        )

    def test_catalogue_candidates_merge_with_local_and_deduplicate(self) -> None:
        remote_data = {
            "source": "steam",
            "degraded": False,
            "has_more": False,
            "items": [
                {
                    "steam_app_id": 1145360,
                    "title": "Hades",
                    "platforms": ["Windows"],
                    "review_score": 95,
                    "source": "steam",
                },
                {
                    "steam_app_id": 900001,
                    "title": "在线动作游戏",
                    "platforms": ["Windows"],
                    "review_score": 91,
                    "cover_url": "https://cdn.example/900001.jpg",
                    "source": "steam",
                },
            ],
        }
        preferences = PreferenceInput(genres=["动作"], platforms=["PC"])

        with patch(
            "backend.src.services.recommend_service.catalogue_service.list_games",
            return_value=remote_data,
        ):
            result = load_recommendation_candidates(preferences, 5)

        app_ids = [item.steam_app_id for item in result]
        self.assertEqual(app_ids.count(1145360), 1)
        self.assertIn(900001, app_ids)
        remote = next(item for item in result if item.steam_app_id == 900001)
        self.assertEqual(remote.platforms, ["PC"])
        self.assertEqual(remote.score, 9.1)
        self.assertEqual(remote.source, "steam")

    def test_catalogue_failure_keeps_local_recommendations_available(self) -> None:
        preferences = PreferenceInput(genres=["动作"], platforms=["PC"])
        with patch(
            "backend.src.services.recommend_service.catalogue_service.list_games",
            side_effect=RuntimeError("Steam unavailable"),
        ):
            result = load_recommendation_candidates(preferences, 5)

        self.assertEqual(len(result), 5)
        self.assertTrue(all(item.source == "local" for item in result))


if __name__ == "__main__":
    unittest.main()
