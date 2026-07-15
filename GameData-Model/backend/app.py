"""Local HTTP service for the game catalogue."""

import html
import json
import os
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
DATA_PATH = Path(__file__).resolve().parent / "data" / "games.json"
DEFAULT_PAGE_SIZE = 12
MAX_PAGE_SIZE = 48

# Steam only exposes artwork for games that have a Steam app id. The catalogue
# still works for console-only and non-Steam games because every item has a
# local SVG fallback served by this module.
STEAM_APP_IDS = {
    "game-001": 413150,
    "game-002": 2358720,
    "game-003": 1426210,
    "game-004": 367520,
    "game-005": 289070,
    "game-007": 1145360,
    "game-008": 1086940,
    "game-010": 105600,
    "game-011": 1091500,
    "game-012": 1245620,
    "game-013": 1174180,
    "game-014": 292030,
    "game-016": 582010,
    "game-017": 1190460,
    "game-018": 814380,
    "game-019": 255710,
    "game-020": 578080,
    "game-021": 730,
    "game-022": 570,
    "game-024": 322330,
    "game-025": 1366540,
    "game-026": 736190,
    "game-027": 1203220,
    "game-028": 1551360,
    "game-029": 2519060,
    "game-030": 477160,
    "game-031": 1222700,
    "game-032": 250900,
    "game-033": 646570,
    "game-034": 457140,
    "game-035": 529340,
    "game-036": 1543030,
    "game-040": 2515020,
    "game-041": 2322010,
    "game-042": 1817190,
    "game-043": 1240440,
    "game-044": 2440510,
    "game-045": 1172620,
    "game-046": 381210,
    "game-049": 2325290,
    "game-051": 2344520,
    "game-052": 238960,
    "game-054": 2357570,
    "game-055": 2054970,
    "game-056": 1151640,
    "game-057": 728880,
    "game-058": 632360,
    "game-059": 1971650,
    "game-060": 535930,
}

COVER_COLORS = (
    ("#0b1021", "#00e5ff"),
    ("#1c1028", "#ff3d9a"),
    ("#10261f", "#60f5a7"),
    ("#261d10", "#ffcc66"),
)


class GameDataRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(FRONTEND_ROOT), **kwargs)

    def do_GET(self) -> None:
        request = urlparse(self.path)
        if request.path == "/api/health":
            self._send_json({"code": 0, "message": "success", "data": {"status": "ok"}})
            return
        if request.path == "/api/games/options":
            self._send_json({"code": 0, "message": "success", "data": self._filter_options()})
            return
        if request.path.startswith("/api/games/") and request.path.endswith("/cover.svg"):
            game_id = unquote(request.path[len("/api/games/") : -len("/cover.svg")])
            game = next((item for item in self._read_games() if item["id"] == game_id), None)
            if game is None:
                self._send_json({"code": 404, "message": "game not found", "data": None}, HTTPStatus.NOT_FOUND)
            else:
                self._send_cover_svg(game)
            return
        if request.path == "/api/games":
            data = self._list_games(parse_qs(request.query))
            self._send_json({"code": 0, "message": "success", "data": data})
            return
        if request.path.startswith("/api/games/"):
            game_id = unquote(request.path.removeprefix("/api/games/"))
            game = next((item for item in self._read_games() if item["id"] == game_id), None)
            if game is None:
                self._send_json({"code": 404, "message": "game not found", "data": None}, HTTPStatus.NOT_FOUND)
            else:
                self._send_json({"code": 0, "message": "success", "data": self._with_cover(game)})
            return
        super().do_GET()

    def _list_games(self, query: dict[str, list[str]]) -> dict[str, object]:
        games = self._read_games()
        keyword = query.get("keyword", [""])[0].strip().casefold()
        genre = query.get("genre", [""])[0]
        platform = query.get("platform", [""])[0]
        tag = query.get("tag", [""])[0]
        sort = query.get("sort", ["rating"])[0]

        if keyword:
            games = [game for game in games if keyword in self._searchable_text(game)]
        if genre:
            games = [game for game in games if game["genre"] == genre]
        if platform:
            games = [game for game in games if platform in game["platforms"]]
        if tag:
            games = [game for game in games if tag in game["tags"]]

        games = self._sort_games(games, sort)
        total = len(games)
        page = self._positive_int(query.get("page", ["1"])[0], default=1)
        size = min(self._positive_int(query.get("size", [str(DEFAULT_PAGE_SIZE)])[0], default=DEFAULT_PAGE_SIZE), MAX_PAGE_SIZE)
        total_pages = (total + size - 1) // size if total else 0
        start = (page - 1) * size
        items = [self._with_cover(game) for game in games[start : start + size]]

        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "has_more": page < total_pages,
        }

    def _filter_options(self) -> dict[str, object]:
        games = self._read_games()
        return {
            "genres": sorted({str(game["genre"]) for game in games}),
            "platforms": sorted({str(platform) for game in games for platform in game["platforms"]}),
            "tags": sorted({str(tag) for game in games for tag in game["tags"]}),
            "total": len(games),
        }

    @staticmethod
    def _sort_games(games: list[dict[str, object]], sort: str) -> list[dict[str, object]]:
        if sort == "price_asc":
            return sorted(games, key=lambda game: (float(game["price"]), -float(game["rating"])))
        if sort == "release_desc":
            return sorted(games, key=lambda game: (str(game["release_date"]), float(game["rating"])), reverse=True)
        if sort == "name":
            return sorted(games, key=lambda game: str(game["name"]).casefold())
        return sorted(games, key=lambda game: (-float(game["rating"]), float(game["price"])))

    @staticmethod
    def _positive_int(value: str, default: int) -> int:
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _read_games() -> list[dict[str, object]]:
        with DATA_PATH.open("r", encoding="utf-8") as source:
            return json.load(source)

    @staticmethod
    def _searchable_text(game: dict[str, object]) -> str:
        values = [game["name"], game["genre"], game["description"], *game["platforms"], *game["tags"]]
        return " ".join(str(value) for value in values).casefold()

    @staticmethod
    def _with_cover(game: dict[str, object]) -> dict[str, object]:
        item = dict(game)
        app_id = STEAM_APP_IDS.get(str(game["id"]))
        fallback_url = f"/api/games/{quote(str(game['id']), safe='')}/cover.svg"
        item["cover"] = {
            "url": f"https://cdn.cloudflare.steamstatic.com/steam/apps/{app_id}/header.jpg" if app_id else None,
            "fallback_url": fallback_url,
            "source": "steam" if app_id else "generated",
            "steam_app_id": app_id,
        }
        return item

    def _send_cover_svg(self, game: dict[str, object]) -> None:
        index = sum(ord(character) for character in str(game["id"])) % len(COVER_COLORS)
        background, accent = COVER_COLORS[index]
        name = html.escape(str(game["name"]))
        genre = html.escape(str(game["genre"]))
        escaped_tags = " ".join(html.escape(str(tag)) for tag in game["tags"][:3])
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540" role="img" aria-label="{name}">
  <rect width="960" height="540" fill="{background}"/>
  <path d="M0 416 L960 144" stroke="{accent}" stroke-width="6" opacity=".8"/>
  <path d="M0 464 L960 192" stroke="{accent}" stroke-width="2" opacity=".45"/>
  <circle cx="790" cy="135" r="148" fill="none" stroke="{accent}" stroke-width="3" opacity=".5"/>
  <text x="64" y="284" fill="#f5f7ff" font-family="Arial, Microsoft YaHei, sans-serif" font-size="52" font-weight="700">{name}</text>
  <text x="68" y="336" fill="{accent}" font-family="Arial, Microsoft YaHei, sans-serif" font-size="26">{genre}</text>
  <text x="68" y="386" fill="#c9d4e5" font-family="Arial, Microsoft YaHei, sans-serif" font-size="21">{escaped_tags}</text>
</svg>'''.encode("utf-8")
        self._send_bytes(svg, "image/svg+xml; charset=utf-8", cache_control="public, max-age=86400")

    def _send_json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        response = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(response, "application/json; charset=utf-8", status)

    def _send_bytes(
        self,
        response: bytes,
        content_type: str,
        status: HTTPStatus = HTTPStatus.OK,
        cache_control: str | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(response)))
        if cache_control:
            self.send_header("Cache-Control", cache_control)
        self.end_headers()
        self.wfile.write(response)


def run_server(open_browser: bool = True) -> None:
    port = int(os.environ.get("PORT", "18800"))
    server = ThreadingHTTPServer(("127.0.0.1", port), GameDataRequestHandler)
    url = f"http://127.0.0.1:{port}"
    print(f"Game data service: {url}")
    if open_browser:
        webbrowser.open_new_tab(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
