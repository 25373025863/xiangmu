"""Run with: py -m unittest tests.test_game_service"""

import unittest

from backend.src.services.game_service import GameService


class GameServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = GameService()

    def test_keyword_search_finds_a_game(self) -> None:
        games = self.service.list_games(keyword="\u609f\u7a7a")
        self.assertEqual([game.name for game in games], ["\u9ed1\u795e\u8bdd\uff1a\u609f\u7a7a"])

    def test_platform_filter_only_returns_matching_platform(self) -> None:
        games = self.service.list_games(platform="\u624b\u673a")
        self.assertTrue(games)
        self.assertTrue(all("\u624b\u673a" in game.platforms for game in games))

    def test_free_price_filter(self) -> None:
        games = self.service.list_games(price_range="\u514d\u8d39")
        self.assertTrue(games)
        self.assertTrue(all(game.price == 0 for game in games))

    def test_tag_filter_only_returns_matching_tag(self) -> None:
        games = self.service.list_games(tag="\u79d1\u5e7b")
        self.assertTrue(games)
        self.assertTrue(all("\u79d1\u5e7b" in game.tags for game in games))


if __name__ == "__main__":
    unittest.main()
