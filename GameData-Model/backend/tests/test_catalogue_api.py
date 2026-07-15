"""Unit coverage for the catalogue-specific HTTP response helpers."""

import unittest

from backend.app import DEFAULT_PAGE_SIZE, GameDataRequestHandler


class CapturingHandler(GameDataRequestHandler):
    def __init__(self) -> None:
        self.response = b""
        self.content_type = ""

    def _send_bytes(self, response: bytes, content_type: str, **_: object) -> None:
        self.response = response
        self.content_type = content_type


class CatalogueApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.handler = CapturingHandler()

    def test_list_response_paginates_after_sorting(self) -> None:
        page = self.handler._list_games({"page": ["2"], "size": ["12"], "sort": ["rating"]})

        self.assertEqual(page["total"], 60)
        self.assertEqual(page["page"], 2)
        self.assertEqual(page["size"], 12)
        self.assertEqual(len(page["items"]), 12)
        self.assertTrue(page["has_more"])
        self.assertNotEqual(page["items"][0]["id"], "game-001")

    def test_invalid_pagination_uses_safe_values(self) -> None:
        page = self.handler._list_games({"page": ["not-a-page"], "size": ["not-a-size"]})

        self.assertEqual(page["page"], 1)
        self.assertEqual(page["size"], DEFAULT_PAGE_SIZE)
        self.assertEqual(len(page["items"]), DEFAULT_PAGE_SIZE)

    def test_items_include_a_remote_or_generated_cover_and_local_fallback(self) -> None:
        item = self.handler._list_games({"keyword": ["星露谷"], "size": ["1"]})["items"][0]

        self.assertEqual(item["cover"]["source"], "steam")
        self.assertIn("steamstatic.com", item["cover"]["url"])
        self.assertEqual(item["cover"]["fallback_url"], "/api/games/game-001/cover.svg")

    def test_genshin_uses_local_cover_without_an_unrelated_steam_app(self) -> None:
        item = self.handler._list_games({"keyword": ["原神"], "size": ["1"]})["items"][0]

        self.assertEqual(item["id"], "game-006")
        self.assertEqual(item["cover"]["source"], "generated")
        self.assertIsNone(item["cover"]["url"])
        self.assertIsNone(item["cover"]["steam_app_id"])
        self.assertEqual(item["cover"]["fallback_url"], "/api/games/game-006/cover.svg")

    def test_no_match_response_is_an_empty_terminal_page(self) -> None:
        page = self.handler._list_games({"keyword": ["绝对不存在的游戏名称"]})

        self.assertEqual(page["items"], [])
        self.assertEqual(page["total"], 0)
        self.assertEqual(page["total_pages"], 0)
        self.assertFalse(page["has_more"])

    def test_local_svg_cover_is_valid_when_remote_artwork_is_unavailable(self) -> None:
        game = next(game for game in self.handler._read_games() if game["id"] == "game-009")

        self.handler._send_cover_svg(game)

        self.assertEqual(self.handler.content_type, "image/svg+xml; charset=utf-8")
        self.assertIn("动物森友会", self.handler.response.decode("utf-8"))
        self.assertIn("<svg", self.handler.response.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
