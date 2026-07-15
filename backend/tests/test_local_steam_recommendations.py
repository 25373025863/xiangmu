import unittest

from backend.src.models.schemas import GameCandidate, PreferenceInput
from backend.src.services.recommend_service import build_demo_recommendations


def candidate(
    title: str,
    *,
    genres: list[str] | None = None,
    platforms: list[str] | None = None,
    steam_app_id: int | None = None,
) -> GameCandidate:
    return GameCandidate(
        title=title,
        genres=genres or [],
        platforms=platforms or [],
        steam_app_id=steam_app_id,
    )


class LocalSteamRecommendationTests(unittest.TestCase):
    def test_owned_games_are_filtered_by_app_id_and_exact_top_game_name(self) -> None:
        preferences = PreferenceInput(
            genres=["动作"],
            platforms=["PC"],
            steam_summary={
                "visibility": "public",
                "game_count": 2,
                "owned_game_app_ids": [1145360],
                "top_games": [{"name": "文明 VI"}],
            },
        )
        games = [
            candidate("哈迪斯", genres=["动作"], platforms=["PC"], steam_app_id=1145360),
            candidate("文明 VI", genres=["策略"], platforms=["PC"]),
            candidate("未拥有的动作游戏", genres=["动作"], platforms=["PC"]),
        ]

        recommendations = build_demo_recommendations(preferences, games, limit=3)

        self.assertEqual([item.title for item in recommendations], ["未拥有的动作游戏"])
        self.assertNotIn("哈迪斯", recommendations[0].similar_games)
        self.assertNotIn("文明 VI", recommendations[0].similar_games)

    def test_inferred_preferences_improve_ranking_without_replacing_manual_preferences(self) -> None:
        games = [
            candidate("手填偏好游戏", genres=["动作"], platforms=["PC"]),
            candidate("无匹配游戏", genres=["休闲"], platforms=["手机"]),
            candidate("Steam 推断游戏", genres=["策略"], platforms=["Switch"]),
        ]
        manual_only = PreferenceInput(genres=["动作"], platforms=["PC"])
        with_steam = PreferenceInput(
            genres=["动作"],
            platforms=["PC"],
            steam_summary={
                "visibility": "public",
                "game_count": 1,
                "top_games": [{"name": "其他已拥有游戏"}],
                "inferred_game_types": ["策略"],
                "suggested_platforms": ["Switch"],
            },
        )

        baseline = build_demo_recommendations(manual_only, games, limit=2)
        enriched = build_demo_recommendations(with_steam, games, limit=2)

        self.assertEqual([item.title for item in baseline], ["手填偏好游戏", "无匹配游戏"])
        self.assertEqual([item.title for item in enriched], ["手填偏好游戏", "Steam 推断游戏"])
        self.assertGreater(enriched[0].match_score, enriched[1].match_score)
        self.assertIn("Steam 游戏库推断", enriched[1].reason)

    def test_private_or_empty_library_does_not_change_local_ranking(self) -> None:
        games = [
            candidate("无匹配游戏", genres=["休闲"], platforms=["手机"]),
            candidate("不会采用的推断", genres=["策略"], platforms=["Switch"]),
        ]
        preferences = PreferenceInput(
            genres=[],
            platforms=[],
            steam_summary={
                "visibility": "private",
                "game_count": 20,
                "inferred_game_types": ["策略"],
                "suggested_platforms": ["Switch"],
            },
        )

        recommendations = build_demo_recommendations(preferences, games, limit=2)

        self.assertEqual([item.title for item in recommendations], ["无匹配游戏", "不会采用的推断"])


if __name__ == "__main__":
    unittest.main()
