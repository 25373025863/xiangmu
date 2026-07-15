import threading
import time
import unittest
from collections.abc import Mapping
from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.src.app import app
from backend.src.routes import catalogue_routes
from backend.src.services.catalogue_service import (
    CatalogueService,
    SteamSearchHTMLParser,
)


def search_row(app_id: int, *, missing_optional_fields: bool = False) -> str:
    optional = ""
    if not missing_optional_fields:
        optional = f"""
          <div class="col search_capsule">
            <img src="//cdn.example.test/{app_id}.jpg" alt="Game {app_id}">
          </div>
          <span class="platform_img win"></span>
          <span class="platform_img linux"></span>
          <div class="col search_released responsive_secondrow">2026 年 7 月 15 日</div>
          <div class="col search_reviewscore responsive_secondrow">
            <span class="search_review_summary positive"
              data-tooltip-html="特别好评&lt;br&gt;92% 的用户评测为好评"></span>
          </div>
          <div class="discount_block" data-price-final="6800">
            <div class="discount_final_price">¥ 68.00</div>
          </div>
        """
    return f"""
      <a class="search_result_row ds_collapse_flag"
         href="https://store.steampowered.com/app/{app_id}/Game_{app_id}/?snr=test"
         data-ds-appid="{app_id}">
        <div class="responsive_search_name_combined">
          <span class="title">Game {app_id}</span>
          {optional}
        </div>
      </a>
    """


def block_html(start: int, count: int = 25) -> str:
    return "".join(search_row(1000 + index) for index in range(start, start + count))


class SteamSearchParserTests(unittest.TestCase):
    def test_extracts_normalized_card_fields_and_tolerates_missing_optional_fields(self) -> None:
        parser = SteamSearchHTMLParser()
        parser.feed(search_row(1234) + search_row(5678, missing_optional_fields=True))
        parser.close()

        first, second = parser.items
        self.assertEqual(first["id"], "steam-1234")
        self.assertEqual(first["steam_app_id"], 1234)
        self.assertEqual(first["title"], "Game 1234")
        self.assertEqual(first["cover_url"], "https://cdn.example.test/1234.jpg")
        self.assertEqual(first["platforms"], ["Windows", "Linux"])
        self.assertEqual(first["review_score"], 92)
        self.assertEqual(first["review_label"], "特别好评")
        self.assertEqual(first["price"], "¥ 68.00")
        self.assertEqual(first["source"], "steam")

        self.assertEqual(second["id"], "steam-5678")
        self.assertEqual(second["cover_url"], "")
        self.assertEqual(second["platforms"], [])
        self.assertIsNone(second["review_score"])
        self.assertEqual(second["price"], "")


class CatalogueServiceTests(unittest.TestCase):
    def test_page_can_cross_fixed_twenty_five_item_blocks(self) -> None:
        requested_starts: list[int] = []

        def fetch(parameters: Mapping[str, str]) -> Mapping[str, Any]:
            start = int(parameters["start"])
            requested_starts.append(start)
            return {
                "success": 1,
                "total_count": 80,
                "results_html": block_html(start),
            }

        service = CatalogueService(fetcher=fetch)
        result = service.list_games(page=2, size=20, sort="topsellers")

        self.assertEqual(requested_starts, [0, 25])
        self.assertEqual(
            [item["steam_app_id"] for item in result["items"]],
            list(range(1020, 1040)),
        )
        self.assertEqual(result["total"], 80)
        self.assertTrue(result["has_more"])
        self.assertEqual(result["source"], "steam")
        self.assertFalse(result["degraded"])

    def test_cached_block_is_reused_until_ttl_expires(self) -> None:
        calls = 0
        clock_value = [10.0]

        def fetch(parameters: Mapping[str, str]) -> Mapping[str, Any]:
            nonlocal calls
            calls += 1
            return {
                "success": 1,
                "total_count": 50,
                "results_html": block_html(int(parameters["start"])),
            }

        service = CatalogueService(
            fetcher=fetch,
            ttl_seconds=30,
            clock=lambda: clock_value[0],
        )
        service.list_games(page=1, size=12)
        service.list_games(page=2, size=12)
        self.assertEqual(calls, 1)

        clock_value[0] = 41.0
        service.list_games(page=1, size=12)
        self.assertEqual(calls, 2)

    def test_cache_and_lock_storage_stay_bounded_for_many_search_keys(self) -> None:
        def fetch(parameters: Mapping[str, str]) -> Mapping[str, Any]:
            return {
                "success": 1,
                "total_count": 1,
                "results_html": search_row(42),
            }

        service = CatalogueService(fetcher=fetch, max_cache_entries=4)

        for index in range(40):
            service.list_games(keyword=f"keyword-{index}", page=1, size=1)

        self.assertLessEqual(len(service._cache), 4)
        self.assertLessEqual(len(service._key_locks), 4)

    def test_expired_entries_are_pruned_when_another_key_is_requested(self) -> None:
        clock_value = [10.0]

        def fetch(parameters: Mapping[str, str]) -> Mapping[str, Any]:
            return {
                "success": 1,
                "total_count": 1,
                "results_html": search_row(42),
            }

        service = CatalogueService(
            fetcher=fetch,
            ttl_seconds=5,
            max_cache_entries=10,
            clock=lambda: clock_value[0],
        )
        service.list_games(keyword="old", page=1, size=1)
        clock_value[0] = 16.0
        service.list_games(keyword="new", page=1, size=1)

        self.assertEqual(len(service._cache), 1)
        self.assertIn(("new", "topsellers", 0), service._cache)

    def test_concurrent_requests_share_the_same_in_flight_block(self) -> None:
        calls = 0
        calls_lock = threading.Lock()
        barrier = threading.Barrier(3)

        def fetch(parameters: Mapping[str, str]) -> Mapping[str, Any]:
            nonlocal calls
            with calls_lock:
                calls += 1
            time.sleep(0.05)
            return {
                "success": 1,
                "total_count": 50,
                "results_html": block_html(int(parameters["start"])),
            }

        service = CatalogueService(fetcher=fetch)

        def run_request() -> None:
            barrier.wait()
            service.list_games(page=1, size=12)

        threads = [threading.Thread(target=run_request) for _ in range(2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(timeout=2)

        self.assertEqual(calls, 1)

    def test_invalid_remote_payload_returns_local_fallback(self) -> None:
        service = CatalogueService(
            fetcher=lambda _: {"success": 0, "results_html": "", "total_count": 0}
        )

        result = service.list_games(page=1, size=3, keyword="")

        self.assertEqual(result["source"], "local")
        self.assertTrue(result["degraded"])
        self.assertEqual(len(result["items"]), 3)
        self.assertIn("Steam 商店暂时无法访问", result["fallback_message"])
        self.assertTrue(any(item["cover_url"].startswith("https://") for item in result["items"]))

    def test_non_object_remote_payload_returns_local_fallback(self) -> None:
        service = CatalogueService(fetcher=lambda _: None)  # type: ignore[arg-type]

        result = service.list_games(page=1, size=1)

        self.assertEqual(result["source"], "local")
        self.assertTrue(result["degraded"])

    def test_request_parameters_include_sort_and_fixed_filters(self) -> None:
        captured: dict[str, str] = {}

        def fetch(parameters: Mapping[str, str]) -> Mapping[str, Any]:
            captured.update(parameters)
            return {"success": 1, "total_count": 1, "results_html": search_row(42)}

        CatalogueService(fetcher=fetch).list_games(sort="released", page=1, size=12)

        self.assertEqual(captured["term"], "")
        self.assertEqual(captured["sort_by"], "Released_DESC")
        self.assertEqual(captured["category1"], "998")
        self.assertEqual(captured["filter"], "topsellers")
        self.assertEqual(captured["infinite"], "1")
        self.assertEqual(captured["cc"], "CN")
        self.assertEqual(captured["l"], "schinese")

    def test_keyword_keeps_reliable_steam_term_filter_when_sorting(self) -> None:
        captured: dict[str, str] = {}

        def fetch(parameters: Mapping[str, str]) -> Mapping[str, Any]:
            captured.update(parameters)
            return {"success": 1, "total_count": 1, "results_html": search_row(42)}

        CatalogueService(fetcher=fetch).list_games(
            keyword="co-op", sort="released", page=1, size=12
        )

        self.assertEqual(captured["term"], "co-op")
        self.assertEqual(captured["sort_by"], "_ASC")


class CatalogueRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_route_uses_standard_success_envelope_and_validates_page_size(self) -> None:
        catalogue_data = {
            "items": [],
            "total": 0,
            "page": 1,
            "size": 12,
            "has_more": False,
            "source": "steam",
            "degraded": False,
        }
        with patch.object(
            catalogue_routes.catalogue_service,
            "list_games",
            return_value=catalogue_data,
        ):
            response = self.client.get("/api/catalogue/games")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["data"], catalogue_data)
        self.assertEqual(
            self.client.get("/api/catalogue/games?size=26").status_code,
            422,
        )


if __name__ == "__main__":
    unittest.main()
