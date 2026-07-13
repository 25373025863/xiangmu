"""Local HTTP service for the game data dashboard."""

import json
import os
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
DATA_PATH = Path(__file__).resolve().parent / "data" / "games.json"


class GameDataRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, directory=str(FRONTEND_ROOT), **kwargs)

    def do_GET(self) -> None:
        request = urlparse(self.path)
        if request.path == "/api/health":
            self._send_json({"code": 0, "message": "success", "data": {"status": "ok"}})
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
                self._send_json({"code": 0, "message": "success", "data": game})
            return
        super().do_GET()

    def _list_games(self, query: dict[str, list[str]]) -> dict[str, object]:
        games = self._read_games()
        keyword = query.get("keyword", [""])[0].strip().casefold()
        genre = query.get("genre", [""])[0]
        platform = query.get("platform", [""])[0]
        tag = query.get("tag", [""])[0]

        if keyword:
            games = [game for game in games if keyword in self._searchable_text(game)]
        if genre:
            games = [game for game in games if game["genre"] == genre]
        if platform:
            games = [game for game in games if platform in game["platforms"]]
        if tag:
            games = [game for game in games if tag in game["tags"]]
        return {"items": games, "total": len(games)}

    @staticmethod
    def _read_games() -> list[dict[str, object]]:
        with DATA_PATH.open("r", encoding="utf-8") as source:
            return json.load(source)

    @staticmethod
    def _searchable_text(game: dict[str, object]) -> str:
        values = [game["name"], game["genre"], game["description"], *game["platforms"], *game["tags"]]
        return " ".join(str(value) for value in values).casefold()

    def _send_json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        response = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)


def run_server(open_browser: bool = True) -> None:
    port = int(os.environ.get("PORT", "8000"))
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
