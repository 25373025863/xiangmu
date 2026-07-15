import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from python.backend.main import HttpPayload, parse_steam_identifier, read_public_steam_profile


PROFILE_XML = b"""<?xml version=\"1.0\"?>
<profile>
  <steamID64>76561198000000000</steamID64>
  <steamID>Test Player</steamID>
  <privacyState>public</privacyState>
</profile>
"""

GAMES_XML = b"""<?xml version=\"1.0\"?>
<gamesList><games><game>
  <appID>10</appID><name>Counter-Strike</name><hoursOnRecord>12.5 hrs on record</hoursOnRecord>
  <genres><genre name=\"Action\" /></genres>
</game></games></gamesList>
"""


def xml_response(body: bytes, url: str = "https://steamcommunity.com/id/test/?xml=1") -> HttpPayload:
    return HttpPayload(body=body, final_url=url, content_type="text/xml")


class SteamServiceTests(unittest.TestCase):
    def test_profile_and_vanity_urls_are_parsed_without_accepting_other_hosts(self) -> None:
        self.assertEqual(
            parse_steam_identifier("https://steamcommunity.com/profiles/76561198000000000/games/?tab=all"),
            ("profiles", "76561198000000000"),
        )
        self.assertEqual(
            parse_steam_identifier("steamcommunity.com/id/test-player/"),
            ("id", "test-player"),
        )
        with self.assertRaises(ValueError):
            parse_steam_identifier("https://notsteamcommunity.com/id/test-player")

    @patch.dict(os.environ, {"STEAM_API_KEY": "test-key"})
    def test_web_api_library_is_preferred_after_profile_resolution(self) -> None:
        calls: list[str] = []

        def fake_fetch(url: str) -> HttpPayload:
            calls.append(url)
            if url.endswith("?xml=1"):
                return xml_response(PROFILE_XML, url)
            if "GetOwnedGames" in url:
                return HttpPayload(
                    body=json.dumps(
                        {
                            "response": {
                                "game_count": 2,
                                "games": [
                                    {"appid": 10, "name": "Counter-Strike", "playtime_forever": 600},
                                    {"appid": 20, "name": "Team Fortress", "playtime_forever": 60},
                                ],
                            }
                        }
                    ).encode(),
                    final_url=url,
                    content_type="application/json",
                )
            if "GetRecentlyPlayedGames" in url:
                return HttpPayload(
                    body=json.dumps(
                        {
                            "response": {
                                "games": [
                                    {"appid": 10, "name": "Counter-Strike", "playtime_2weeks": 120}
                                ]
                            }
                        }
                    ).encode(),
                    final_url=url,
                    content_type="application/json",
                )
            self.fail(f"unexpected Steam URL: {url}")

        with patch("python.backend.main.fetch_response", side_effect=fake_fetch):
            summary = read_public_steam_profile("https://steamcommunity.com/id/test-player/")

        self.assertEqual(summary.visibility, "public")
        self.assertEqual(summary.data_source, "steam_web_api")
        self.assertEqual(summary.game_count, 2)
        self.assertEqual(summary.top_games[0]["app_id"], 10)
        self.assertEqual(summary.recent_games[0]["hours_played"], 2.0)
        self.assertFalse(any("/games/?tab=all" in url for url in calls))

    @patch.dict(os.environ, {"STEAM_API_KEY": ""})
    def test_login_redirect_is_not_mistaken_for_an_empty_public_xml_library(self) -> None:
        def fake_fetch(url: str) -> HttpPayload:
            if url.endswith("?xml=1") and "/games/" not in url:
                return xml_response(PROFILE_XML, url)
            if "/games/?tab=all" in url:
                return HttpPayload(
                    body=b"<!DOCTYPE html><html><body>Steam login</body></html>",
                    final_url="https://steamcommunity.com/login/?redir=games",
                    content_type="text/html",
                )
            self.fail(f"unexpected Steam URL: {url}")

        with patch("python.backend.main.fetch_response", side_effect=fake_fetch):
            summary = read_public_steam_profile("76561198000000000")

        self.assertEqual(summary.visibility, "public")
        self.assertEqual(summary.data_source, "profile_only")
        self.assertEqual(summary.game_count, 0)
        self.assertIn("STEAM_API_KEY", summary.message)

    @patch.dict(os.environ, {"STEAM_API_KEY": ""})
    def test_legacy_public_xml_remains_a_compatibility_fallback(self) -> None:
        def fake_fetch(url: str) -> HttpPayload:
            if url.endswith("?xml=1") and "/games/" not in url:
                return xml_response(PROFILE_XML, url)
            if "/games/?tab=all" in url:
                return xml_response(GAMES_XML, url)
            self.fail(f"unexpected Steam URL: {url}")

        with patch("python.backend.main.fetch_response", side_effect=fake_fetch):
            summary = read_public_steam_profile("76561198000000000")

        self.assertEqual(summary.data_source, "public_xml")
        self.assertEqual(summary.game_count, 1)
        self.assertEqual(summary.inferred_game_types, ["动作"])
        self.assertEqual(summary.total_playtime_hours, 12.5)

    @patch.dict(os.environ, {"STEAM_API_KEY": "test-key"})
    def test_vanity_url_can_fall_back_to_web_api_when_profile_xml_is_unavailable(self) -> None:
        def fake_fetch(url: str) -> HttpPayload:
            if url.endswith("?xml=1"):
                raise URLError("Steam profile XML unavailable")
            if "ResolveVanityURL" in url:
                return HttpPayload(
                    body=b'{"response":{"success":1,"steamid":"76561198000000000"}}',
                    final_url=url,
                    content_type="application/json",
                )
            if "GetOwnedGames" in url:
                return HttpPayload(
                    body=b'{"response":{"game_count":1,"games":[{"appid":10,"name":"Counter-Strike","playtime_forever":60}]}}',
                    final_url=url,
                    content_type="application/json",
                )
            if "GetRecentlyPlayedGames" in url:
                return HttpPayload(
                    body=b'{"response":{"games":[]}}',
                    final_url=url,
                    content_type="application/json",
                )
            self.fail(f"unexpected Steam URL: {url}")

        with patch("python.backend.main.fetch_response", side_effect=fake_fetch):
            summary = read_public_steam_profile("test-player")

        self.assertEqual(summary.steam_id64, "76561198000000000")
        self.assertEqual(summary.data_source, "steam_web_api")
        self.assertEqual(summary.game_count, 1)

    @patch.dict(os.environ, {"STEAM_API_KEY": "test-key"})
    def test_profile_xml_403_falls_back_to_web_api_for_steam_id64(self) -> None:
        calls: list[str] = []

        def fake_fetch(url: str) -> HttpPayload:
            calls.append(url)
            if url.startswith("https://steamcommunity.com/"):
                raise HTTPError(url, 403, "Forbidden", None, None)
            if "GetOwnedGames" in url:
                return HttpPayload(
                    body=b'{"response":{"game_count":1,"games":[{"appid":10,"name":"Counter-Strike","playtime_forever":60}]}}',
                    final_url=url,
                    content_type="application/json",
                )
            if "GetRecentlyPlayedGames" in url:
                return HttpPayload(
                    body=b'{"response":{"games":[]}}',
                    final_url=url,
                    content_type="application/json",
                )
            self.fail(f"unexpected Steam URL: {url}")

        with patch("python.backend.main.fetch_response", side_effect=fake_fetch):
            summary = read_public_steam_profile("76561198000000000")

        self.assertEqual(summary.data_source, "steam_web_api")
        self.assertEqual(summary.game_count, 1)
        self.assertTrue(any("GetOwnedGames" in url for url in calls))

    @patch.dict(os.environ, {"STEAM_API_KEY": "test-key"})
    def test_profile_xml_429_resolves_vanity_and_falls_back_to_web_api(self) -> None:
        calls: list[str] = []

        def fake_fetch(url: str) -> HttpPayload:
            calls.append(url)
            if url.startswith("https://steamcommunity.com/"):
                raise HTTPError(url, 429, "Too Many Requests", None, None)
            if "ResolveVanityURL" in url:
                return HttpPayload(
                    body=b'{"response":{"success":1,"steamid":"76561198000000000"}}',
                    final_url=url,
                    content_type="application/json",
                )
            if "GetOwnedGames" in url:
                return HttpPayload(
                    body=b'{"response":{"game_count":1,"games":[{"appid":10,"name":"Counter-Strike","playtime_forever":60}]}}',
                    final_url=url,
                    content_type="application/json",
                )
            if "GetRecentlyPlayedGames" in url:
                return HttpPayload(
                    body=b'{"response":{"games":[]}}',
                    final_url=url,
                    content_type="application/json",
                )
            self.fail(f"unexpected Steam URL: {url}")

        with patch("python.backend.main.fetch_response", side_effect=fake_fetch):
            summary = read_public_steam_profile("test-player")

        self.assertEqual(summary.steam_id64, "76561198000000000")
        self.assertEqual(summary.data_source, "steam_web_api")
        self.assertEqual(summary.game_count, 1)
        self.assertTrue(any("ResolveVanityURL" in url for url in calls))
        self.assertTrue(any("GetOwnedGames" in url for url in calls))

    @patch.dict(os.environ, {"STEAM_API_KEY": "test-key"})
    def test_profile_xml_404_remains_not_found_without_web_api_fallback(self) -> None:
        calls: list[str] = []

        def fake_fetch(url: str) -> HttpPayload:
            calls.append(url)
            raise HTTPError(url, 404, "Not Found", None, None)

        with patch("python.backend.main.fetch_response", side_effect=fake_fetch):
            summary = read_public_steam_profile("76561198000000000")

        self.assertEqual(summary.visibility, "not_found")
        self.assertFalse(any("api.steampowered.com" in url for url in calls))


if __name__ == "__main__":
    unittest.main()
