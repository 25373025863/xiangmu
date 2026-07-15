"""Online game catalogue backed by Steam Store search results."""

from __future__ import annotations

import html
import json
import socket
import threading
import time
import urllib.error
import urllib.request
from collections import OrderedDict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlencode, urljoin, urlparse

from backend.src.services.game_service import GameService


STEAM_SEARCH_URL = "https://store.steampowered.com/search/results/"
STEAM_BLOCK_SIZE = 25
DEFAULT_CACHE_TTL_SECONDS = 300.0
DEFAULT_CACHE_MAX_ENTRIES = 256
DEFAULT_LOCK_STRIPES = 64

SORT_PARAMETERS = {
    "topsellers": "_ASC",
    "released": "Released_DESC",
    "price": "Price_ASC",
    "name": "Name_ASC",
}

LOCAL_STEAM_APP_IDS = {
    "g001": 413150,  # Stardew Valley
    "g002": 1426210,  # It Takes Two
    "g003": 1145360,  # Hades
    "g005": 289070,  # Sid Meier's Civilization VI
}


class CatalogueRemoteError(RuntimeError):
    """Raised when Steam cannot provide a usable catalogue block."""


@dataclass(frozen=True)
class _RemoteBlock:
    items: list[dict[str, Any]]
    total: int


@dataclass(frozen=True)
class _CacheEntry:
    expires_at: float
    block: _RemoteBlock


@dataclass
class _ParsedRow:
    app_id: int | None = None
    store_url: str = ""
    cover_url: str = ""
    image_alt: str = ""
    platforms: list[str] = field(default_factory=list)
    final_price_cents: int | None = None
    review_tooltip: str = ""
    review_label: str = ""
    text: dict[str, list[str]] = field(
        default_factory=lambda: {
            "title": [],
            "release": [],
            "review": [],
            "final_price": [],
            "price": [],
        }
    )


class _PlainTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        cleaned = " ".join(data.split())
        if cleaned:
            self.parts.append(cleaned)


class SteamSearchHTMLParser(HTMLParser):
    """Parse Steam search cards without depending on Steam's CSS layout."""

    _VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
    _PLATFORM_NAMES = {
        "win": "Windows",
        "mac": "macOS",
        "linux": "Linux",
        "vr_supported": "VR",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.items: list[dict[str, Any]] = []
        self._current: _ParsedRow | None = None
        self._elements: list[tuple[str, str | None, bool]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        classes = set(attributes.get("class", "").split())
        is_row = tag == "a" and "search_result_row" in classes

        if is_row:
            if self._current is not None:
                self._finish_row()
            self._current = _ParsedRow(
                app_id=_app_id_from_attributes(attributes),
                store_url=_absolute_url(attributes.get("href", "")),
            )

        if self._current is None:
            return

        capture: str | None = None
        if "title" in classes:
            capture = "title"
        elif "search_released" in classes:
            capture = "release"
        elif "search_review_summary" in classes:
            capture = "review"
        elif "discount_final_price" in classes:
            capture = "final_price"
        elif "search_price" in classes:
            capture = "price"

        if tag == "img" and not self._current.cover_url:
            self._current.cover_url = _absolute_url(
                attributes.get("src", "") or attributes.get("data-src", "")
            )
            self._current.image_alt = _clean_text(attributes.get("alt", ""))

        if tag == "span":
            for css_class, platform_name in self._PLATFORM_NAMES.items():
                if css_class in classes and platform_name not in self._current.platforms:
                    self._current.platforms.append(platform_name)

        price_value = attributes.get("data-price-final", "").strip()
        if price_value.isdigit():
            self._current.final_price_cents = int(price_value)

        tooltip = (
            attributes.get("data-tooltip-html", "")
            or attributes.get("data-tooltip-text", "")
            or attributes.get("aria-label", "")
        )
        if tooltip and "search_review_summary" in classes:
            self._current.review_tooltip = tooltip
            tooltip_parts = _html_text_parts(tooltip)
            if tooltip_parts:
                self._current.review_label = tooltip_parts[0]

        if tag not in self._VOID_TAGS:
            self._elements.append((tag, capture, is_row))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        if self._current is None:
            return
        cleaned = _clean_text(data)
        if not cleaned:
            return
        for _, capture, _ in reversed(self._elements):
            if capture:
                self._current.text[capture].append(cleaned)
                return

    def handle_endtag(self, tag: str) -> None:
        if self._current is None:
            return
        matching_index = next(
            (
                index
                for index in range(len(self._elements) - 1, -1, -1)
                if self._elements[index][0] == tag
            ),
            None,
        )
        if matching_index is None:
            return
        closed_elements = self._elements[matching_index:]
        del self._elements[matching_index:]
        if any(is_row for _, _, is_row in closed_elements):
            self._finish_row()

    def close(self) -> None:
        super().close()
        if self._current is not None:
            self._finish_row()

    def _finish_row(self) -> None:
        row = self._current
        self._current = None
        self._elements.clear()
        if row is None:
            return

        app_id = row.app_id or _app_id_from_url(row.store_url)
        if app_id is None:
            return

        title = _join_text(row.text["title"]) or row.image_alt
        if not title:
            title = f"Steam 游戏 {app_id}"
        release_date = _join_text(row.text["release"])
        review_text = row.review_tooltip or _join_text(row.text["review"])
        review_label = row.review_label or _join_text(row.text["review"])
        final_price = _join_text(row.text["final_price"])
        price = final_price or _join_text(row.text["price"])
        if not price and row.final_price_cents is not None:
            price = (
                "免费开玩"
                if row.final_price_cents == 0
                else f"¥ {row.final_price_cents / 100:.2f}"
            )

        self.items.append(
            {
                "id": f"steam-{app_id}",
                "steam_app_id": app_id,
                "title": title,
                "cover_url": row.cover_url,
                "store_url": row.store_url
                or f"https://store.steampowered.com/app/{app_id}/",
                "platforms": row.platforms,
                "release_date": release_date,
                "review_score": _extract_percentage(review_text),
                "review_label": review_label,
                "price": price,
                "source": "steam",
            }
        )


class CatalogueService:
    def __init__(
        self,
        fetcher: Callable[[Mapping[str, str]], Mapping[str, Any]] | None = None,
        *,
        ttl_seconds: float = DEFAULT_CACHE_TTL_SECONDS,
        max_cache_entries: int = DEFAULT_CACHE_MAX_ENTRIES,
        clock: Callable[[], float] = time.monotonic,
        game_service: GameService | None = None,
    ) -> None:
        self._fetcher = fetcher or self._fetch_steam_payload
        self._ttl_seconds = max(0.0, ttl_seconds)
        self._max_cache_entries = max(1, int(max_cache_entries))
        self._clock = clock
        self._game_service = game_service or GameService()
        self._cache: OrderedDict[tuple[str, str, int], _CacheEntry] = OrderedDict()
        self._cache_lock = threading.RLock()
        stripe_count = min(DEFAULT_LOCK_STRIPES, self._max_cache_entries)
        self._key_locks = tuple(threading.Lock() for _ in range(stripe_count))

    def list_games(
        self,
        *,
        keyword: str = "",
        sort: str = "topsellers",
        page: int = 1,
        size: int = 12,
    ) -> dict[str, Any]:
        keyword = keyword.strip()
        start = (page - 1) * size
        end = start + size
        first_block = (start // STEAM_BLOCK_SIZE) * STEAM_BLOCK_SIZE
        last_block = ((end - 1) // STEAM_BLOCK_SIZE) * STEAM_BLOCK_SIZE
        # Steam currently drops the term filter for non-default sort values.
        # Keep its reliable relevance order for a search, then sort only the
        # page that is already known to match the requested keyword.
        remote_sort = "topsellers" if keyword else sort

        try:
            blocks = [
                self._get_block(keyword, remote_sort, block_start)
                for block_start in range(
                    first_block, last_block + STEAM_BLOCK_SIZE, STEAM_BLOCK_SIZE
                )
            ]
            combined = [item for block in blocks for item in block.items]
            relative_start = start - first_block
            items = combined[relative_start : relative_start + size]
            if keyword and sort != "topsellers":
                items = _sort_keyword_page(items, sort)
            total = blocks[0].total if blocks else 0
            return {
                "items": items,
                "total": total,
                "page": page,
                "size": size,
                "has_more": start + len(items) < total,
                "source": "steam",
                "degraded": False,
            }
        except (CatalogueRemoteError, OSError, ValueError, TypeError) as exc:
            return self._local_fallback(
                keyword=keyword,
                sort=sort,
                page=page,
                size=size,
                reason=str(exc),
            )

    def clear_cache(self) -> None:
        with self._cache_lock:
            self._cache.clear()

    def _get_block(self, keyword: str, sort: str, start: int) -> _RemoteBlock:
        cache_key = (keyword.casefold(), sort, start)
        now = self._clock()
        with self._cache_lock:
            cached_block = self._cached_block(cache_key, now)
            if cached_block is not None:
                return cached_block
        key_lock = self._key_locks[hash(cache_key) % len(self._key_locks)]

        # Only one request per search block reaches Steam at a time. Other
        # callers re-check the cache after the active request completes.
        with key_lock:
            now = self._clock()
            with self._cache_lock:
                cached_block = self._cached_block(cache_key, now)
                if cached_block is not None:
                    return cached_block

            return self._fetch_block(keyword, sort, start, cache_key)

    def _cached_block(
        self,
        cache_key: tuple[str, str, int],
        now: float,
    ) -> _RemoteBlock | None:
        self._prune_expired_cache(now)
        cached = self._cache.get(cache_key)
        if cached is None:
            return None
        self._cache.move_to_end(cache_key)
        return cached.block

    def _prune_expired_cache(self, now: float) -> None:
        expired_keys = [
            key for key, entry in self._cache.items() if entry.expires_at <= now
        ]
        for key in expired_keys:
            self._cache.pop(key, None)

    def _fetch_block(
        self,
        keyword: str,
        sort: str,
        start: int,
        cache_key: tuple[str, str, int],
    ) -> _RemoteBlock:

        parameters = {
            "term": keyword,
            "start": str(start),
            "count": str(STEAM_BLOCK_SIZE),
            "category1": "998",
            "filter": "topsellers",
            "infinite": "1",
            "cc": "CN",
            "l": "schinese",
            "sort_by": SORT_PARAMETERS[sort],
        }
        try:
            payload = self._fetcher(parameters)
        except (TimeoutError, socket.timeout, urllib.error.URLError, OSError) as exc:
            raise CatalogueRemoteError("Steam 商店连接超时或不可用") from exc

        if not isinstance(payload, Mapping):
            raise CatalogueRemoteError("Steam 商店响应格式无效")
        if payload.get("success") not in (1, "1", True):
            raise CatalogueRemoteError("Steam 商店返回了无效状态")
        results_html = payload.get("results_html")
        if not isinstance(results_html, str):
            raise CatalogueRemoteError("Steam 商店响应缺少游戏列表")

        parser = SteamSearchHTMLParser()
        try:
            parser.feed(results_html)
            parser.close()
        except (ValueError, TypeError) as exc:
            raise CatalogueRemoteError("Steam 游戏列表解析失败") from exc

        total = _coerce_total(payload.get("total_count"), start + len(parser.items))
        if results_html.strip() and not parser.items and total > start:
            raise CatalogueRemoteError("Steam 游戏列表结构暂时无法识别")
        block = _RemoteBlock(items=parser.items, total=total)
        if self._ttl_seconds > 0:
            now = self._clock()
            with self._cache_lock:
                self._prune_expired_cache(now)
                self._cache[cache_key] = _CacheEntry(
                    expires_at=now + self._ttl_seconds,
                    block=block,
                )
                self._cache.move_to_end(cache_key)
                while len(self._cache) > self._max_cache_entries:
                    self._cache.popitem(last=False)
        return block

    @staticmethod
    def _fetch_steam_payload(parameters: Mapping[str, str]) -> Mapping[str, Any]:
        request = urllib.request.Request(
            f"{STEAM_SEARCH_URL}?{urlencode(parameters)}",
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/126 Safari/537.36"
                ),
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                status = getattr(response, "status", None)
                if status is None:
                    status = response.getcode()
                if status != 200:
                    raise CatalogueRemoteError(f"Steam 商店返回 HTTP {status}")
                raw_payload = response.read().decode("utf-8")
        except (TimeoutError, socket.timeout, urllib.error.URLError, OSError) as exc:
            raise CatalogueRemoteError("Steam 商店连接超时或不可用") from exc
        try:
            payload = json.loads(raw_payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise CatalogueRemoteError("Steam 商店返回了无法解析的内容") from exc
        if not isinstance(payload, dict):
            raise CatalogueRemoteError("Steam 商店响应格式无效")
        return payload

    def _local_fallback(
        self,
        *,
        keyword: str,
        sort: str,
        page: int,
        size: int,
        reason: str,
    ) -> dict[str, Any]:
        games = self._game_service.list_games(keyword=keyword)
        items = [self._normalize_local_game(game) for game in games]
        if sort == "name":
            items.sort(key=lambda item: item["title"].casefold())
        elif sort == "price":
            items.sort(key=lambda item: _price_number(item["price"]))
        elif sort == "released":
            items.sort(key=lambda item: item["release_date"], reverse=True)

        total = len(items)
        start = (page - 1) * size
        page_items = items[start : start + size]
        message = "Steam 商店暂时无法访问，正在展示本地游戏。"
        if reason:
            message = f"{message}（{reason}）"
        return {
            "items": page_items,
            "total": total,
            "page": page,
            "size": size,
            "has_more": start + len(page_items) < total,
            "source": "local",
            "degraded": True,
            "fallback_message": message,
        }

    @staticmethod
    def _normalize_local_game(game: Mapping[str, Any]) -> dict[str, Any]:
        game_id = str(game.get("id", ""))
        app_id = LOCAL_STEAM_APP_IDS.get(game_id)
        return {
            "id": game_id,
            "steam_app_id": app_id,
            "title": str(game.get("title", "")),
            "cover_url": (
                f"https://cdn.cloudflare.steamstatic.com/steam/apps/{app_id}/header.jpg"
                if app_id
                else ""
            ),
            "store_url": (
                f"https://store.steampowered.com/app/{app_id}/" if app_id else ""
            ),
            "platforms": list(game.get("platforms", [])),
            "release_date": str(game.get("release_date", "")),
            "review_score": (
                round(float(game["score"]) * 10) if game.get("score") is not None else None
            ),
            "review_label": "本地评分" if game.get("score") is not None else "",
            "price": game.get("price", ""),
            "source": "local",
        }


def _clean_text(value: str) -> str:
    return " ".join(html.unescape(value).split())


def _join_text(parts: list[str]) -> str:
    return _clean_text(" ".join(parts))


def _html_text_parts(value: str) -> list[str]:
    parser = _PlainTextParser()
    parser.feed(html.unescape(value))
    parser.close()
    return parser.parts


def _absolute_url(value: str) -> str:
    value = html.unescape(value.strip())
    if value.startswith("//"):
        return f"https:{value}"
    return urljoin("https://store.steampowered.com", value) if value else ""


def _app_id_from_attributes(attributes: Mapping[str, str]) -> int | None:
    raw_app_ids = attributes.get("data-ds-appid", "")
    for value in raw_app_ids.split(","):
        candidate = value.strip()
        if candidate.isdigit():
            return int(candidate)
    return _app_id_from_url(attributes.get("href", ""))


def _app_id_from_url(value: str) -> int | None:
    path_parts = [part for part in urlparse(value).path.split("/") if part]
    for index, part in enumerate(path_parts[:-1]):
        if part.casefold() == "app" and path_parts[index + 1].isdigit():
            return int(path_parts[index + 1])
    return None


def _extract_percentage(value: str) -> int | None:
    decoded = html.unescape(value)
    for marker in ("%", "％"):
        marker_index = decoded.find(marker)
        if marker_index < 0:
            continue
        start = marker_index
        while start > 0 and decoded[start - 1].isdigit():
            start -= 1
        digits = decoded[start:marker_index]
        if digits:
            return min(100, int(digits))
    return None


def _coerce_total(value: Any, fallback: int) -> int:
    try:
        return max(0, int(str(value).replace(",", "").strip()))
    except (TypeError, ValueError):
        return max(0, fallback)


def _price_number(value: Any) -> float:
    normalized = str(value).casefold()
    if "免费" in normalized or "free" in normalized:
        return 0.0
    characters: list[str] = []
    decimal_seen = False
    for character in str(value):
        if character.isdigit():
            characters.append(character)
        elif character == "." and characters and not decimal_seen:
            characters.append(character)
            decimal_seen = True
    try:
        return float("".join(characters))
    except ValueError:
        return float("inf")


def _sort_keyword_page(items: list[dict[str, Any]], sort: str) -> list[dict[str, Any]]:
    if sort == "name":
        return sorted(items, key=lambda item: str(item.get("title", "")).casefold())
    if sort == "price":
        return sorted(items, key=lambda item: _price_number(item.get("price", "")))
    if sort == "released":
        return sorted(
            items,
            key=lambda item: _release_sort_key(str(item.get("release_date", ""))),
            reverse=True,
        )
    return items


def _release_sort_key(value: str) -> datetime:
    cleaned = _clean_text(value)
    for date_format in ("%Y-%m-%d", "%Y/%m/%d", "%d %b, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(cleaned, date_format)
        except ValueError:
            pass

    numbers: list[int] = []
    digits: list[str] = []
    for character in cleaned:
        if character.isdigit():
            digits.append(character)
        elif digits:
            numbers.append(int("".join(digits)))
            digits = []
    if digits:
        numbers.append(int("".join(digits)))
    if len(numbers) >= 3:
        year, month, day = numbers[:3]
        try:
            return datetime(year, month, day)
        except ValueError:
            pass
    return datetime.min
