"""GAME//PULSE 用户偏好与 Steam 公开资料接口。"""

from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

Platform = Literal["PC", "Switch", "PS5", "Xbox", "手机"]
GameType = Literal["动作", "RPG", "射击", "策略", "模拟经营", "休闲", "独立游戏"]
PlayerMode = Literal["单人", "本地多人", "在线多人", "MMO"]
DurationPreference = Literal["短平快(<10h)", "适中(10-30h)", "杀时间(30h+)", "无限游玩"]
Budget = Literal["免费", "100元内", "100-300元", "300元以上"]

GENRE_MAP = {
    "Action": "动作", "Adventure": "动作", "RPG": "RPG", "Role-Playing": "RPG",
    "Shooter": "射击", "Strategy": "策略", "Simulation": "模拟经营",
    "Casual": "休闲", "Indie": "独立游戏",
}


class UserPreference(BaseModel):
    """推荐模块消费的规范化用户偏好。"""

    platforms: list[Platform] = Field(min_length=1, max_length=5)
    game_types: list[GameType] = Field(min_length=1, max_length=7)
    player_mode: PlayerMode = "单人"
    art_styles: list[str] = Field(default_factory=list, max_length=8)
    duration_preference: DurationPreference = "适中(10-30h)"
    budget: Budget = "100元内"
    chinese_required: bool = False
    notes: str | None = Field(default=None, max_length=1000)
    steam_summary: "SteamPreferenceSummary | None" = None

    @field_validator("platforms", "game_types", "art_styles")
    @classmethod
    def unique_values(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("选项不能重复")
        return values

    @field_validator("notes")
    @classmethod
    def clean_notes(cls, value: str | None) -> str | None:
        return value.strip() if value and value.strip() else None


class SteamProfileRequest(BaseModel):
    steam_identifier: str = Field(min_length=2, max_length=300, description="SteamID、SteamID64、个人资料链接或自定义 URL")

    @field_validator("steam_identifier")
    @classmethod
    def clean_identifier(cls, value: str) -> str:
        return value.strip()


class SteamPreferenceSummary(BaseModel):
    steam_id64: str
    profile_name: str | None = None
    profile_url: str | None = None
    visibility: Literal["public", "private", "not_found", "unavailable"]
    game_count: int = 0
    total_playtime_hours: float = 0
    top_games: list[dict[str, object]] = Field(default_factory=list)
    recent_games: list[dict[str, object]] = Field(default_factory=list)
    owned_game_app_ids: list[int] = Field(default_factory=list)
    inferred_game_types: list[GameType] = Field(default_factory=list)
    suggested_player_mode: PlayerMode | None = None
    suggested_platforms: list[Platform] = Field(default_factory=lambda: ["PC"])
    data_source: Literal["steam_web_api", "public_xml", "profile_only"] = "profile_only"
    message: str


class PreferenceSubmitRequest(UserPreference):
    """接受手填偏好，也可携带已解析的 Steam 摘要。"""


app = FastAPI(title="GAME//PULSE API", description="用户偏好和 Steam 公开资料读取接口", version="2.0.0")
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
FRONTEND_FILE = PROJECT_DIR / "frontend" / "index.html"

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"],
)


def parse_steam_identifier(raw: str) -> tuple[str, str]:
    """返回 URL 资料段类型和标识；支持 ID、ID64、profiles/ 与 id/ 链接。"""
    value = raw.strip().rstrip("/")
    if re.fullmatch(r"\d{17}", value):
        return "profiles", value
    match = re.fullmatch(r"STEAM_[0-5]:[01]:\d+", value, re.IGNORECASE)
    if match:
        # Steam2 ID: account_id + 76561197960265728
        universe, parity, account = value.upper().split(":")
        return "profiles", str(76561197960265728 + int(account) * 2 + int(parity))
    match = re.search(r"steamcommunity\.com/(profiles|id)/([^/?#]+)", value, re.IGNORECASE)
    if match:
        return match.group(1).lower(), match.group(2)
    if re.fullmatch(r"[A-Za-z0-9_-]{2,100}", value):
        return "id", value
    raise ValueError("请输入有效的 SteamID、SteamID64、个人资料链接或自定义 URL")


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "GAME-PULSE/2.0 (public-profile reader)"})
    with urlopen(request, timeout=8) as response:
        return response.read()


def fetch_json(url: str) -> dict[str, object]:
    return json.loads(fetch(url).decode("utf-8"))


def text(element: ET.Element | None, tag: str) -> str | None:
    node = element.find(tag) if element is not None else None
    return node.text.strip() if node is not None and node.text else None


def game_record(app_id: int | None, name: str | None, minutes: int | float) -> dict[str, object] | None:
    if not name:
        return None
    return {
        "app_id": app_id,
        "name": name,
        "hours_played": round(float(minutes) / 60, 1),
    }


def read_steam_web_api_library(steam_id64: str) -> tuple[list[dict[str, object]], list[dict[str, object]]] | None:
    """读取官方 API 的已拥有和最近游玩游戏；缺少服务端 Key 时返回 None。"""
    api_key = os.getenv("STEAM_API_KEY")
    if not api_key:
        return None

    owned_query = urlencode({
        "key": api_key, "steamid": steam_id64, "include_appinfo": "1",
        "include_played_free_games": "1",
    })
    recent_query = urlencode({"key": api_key, "steamid": steam_id64, "format": "json"})
    owned_payload = fetch_json(f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?{owned_query}")
    recent_payload = fetch_json(f"https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?{recent_query}")
    owned_response = owned_payload.get("response", {})
    recent_response = recent_payload.get("response", {})
    owned_games = owned_response.get("games", []) if isinstance(owned_response, dict) else []
    recent_games = recent_response.get("games", []) if isinstance(recent_response, dict) else []

    normalized_owned = [
        game_record(game.get("appid"), game.get("name"), game.get("playtime_forever", 0))
        for game in owned_games if isinstance(game, dict)
    ]
    normalized_recent = [
        game_record(game.get("appid"), game.get("name"), game.get("playtime_2weeks", 0))
        for game in recent_games if isinstance(game, dict)
    ]
    return ([game for game in normalized_owned if game], [game for game in normalized_recent if game])


def read_public_steam_profile(raw_identifier: str) -> SteamPreferenceSummary:
    try:
        segment, identifier = parse_steam_identifier(raw_identifier)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    profile_url = f"https://steamcommunity.com/{segment}/{quote(identifier, safe='')}/"
    try:
        root = ET.fromstring(fetch(f"{profile_url}?xml=1"))
    except HTTPError as error:
        if error.code == 404:
            return SteamPreferenceSummary(steam_id64=identifier if segment == "profiles" else "", visibility="not_found", profile_url=profile_url, message="未找到该 Steam 个人资料。")
        return SteamPreferenceSummary(steam_id64=identifier if segment == "profiles" else "", visibility="unavailable", profile_url=profile_url, message="Steam 暂时无法响应，请稍后重试。")
    except (URLError, ET.ParseError, TimeoutError):
        return SteamPreferenceSummary(steam_id64=identifier if segment == "profiles" else "", visibility="unavailable", profile_url=profile_url, message="无法连接 Steam，请检查网络后重试。")

    steam_id64 = text(root, "steamID64") or (identifier if segment == "profiles" else "")
    profile_name = text(root, "steamID")
    privacy = text(root, "privacyState")
    if privacy and privacy.lower() != "public":
        return SteamPreferenceSummary(steam_id64=steam_id64, profile_name=profile_name, profile_url=profile_url, visibility="private", message="该 Steam 资料或游戏库不可见，请将资料和游戏详情设为公开。")

    games_url = f"https://steamcommunity.com/{segment}/{quote(identifier, safe='')}/games/?tab=all&xml=1"
    try:
        games_root = ET.fromstring(fetch(games_url))
    except (HTTPError, URLError, ET.ParseError, TimeoutError):
        return SteamPreferenceSummary(steam_id64=steam_id64, profile_name=profile_name, profile_url=profile_url, visibility="public", message="已读取公开资料，但游戏库未公开或暂时不可读取；你仍可手动填写偏好。")

    games = games_root.findall(".//game")
    genres: Counter[str] = Counter()
    owned_games: list[dict[str, object]] = []
    multiplayer = False
    for game in games:
        name = text(game, "name")
        app_id_raw = text(game, "appID")
        app_id = int(app_id_raw) if app_id_raw and app_id_raw.isdigit() else None
        hours_raw = text(game, "hoursOnRecord") or "0"
        try:
            hours = float(re.sub(r"[^\d.]", "", hours_raw) or 0)
        except ValueError:
            hours = 0
        for genre in game.findall(".//genre"):
            mapped = GENRE_MAP.get((genre.get("name") or genre.text or "").strip())
            if mapped:
                genres[mapped] += 1
        if any(token in (name or "").lower() for token in ("online", "multiplayer", "co-op")):
            multiplayer = True
        record = game_record(app_id, name, hours * 60)
        if record:
            owned_games.append(record)

    data_source = "public_xml"
    recent_games: list[dict[str, object]] = []
    try:
        api_library = read_steam_web_api_library(steam_id64)
    except (HTTPError, URLError, ValueError, TimeoutError, json.JSONDecodeError):
        api_library = None
    if api_library is not None:
        owned_games, recent_games = api_library
        data_source = "steam_web_api"

    owned_games.sort(key=lambda item: float(item["hours_played"]), reverse=True)
    inferred = [genre for genre, _ in genres.most_common(3)]
    return SteamPreferenceSummary(
        steam_id64=steam_id64, profile_name=profile_name, profile_url=profile_url, visibility="public",
        game_count=len(owned_games), total_playtime_hours=round(sum(float(game["hours_played"]) for game in owned_games), 1),
        top_games=owned_games[:5], recent_games=recent_games[:5],
        owned_game_app_ids=[int(game["app_id"]) for game in owned_games if isinstance(game.get("app_id"), int)],
        inferred_game_types=inferred,
        suggested_player_mode="在线多人" if multiplayer else "单人",
        data_source=data_source,
        message="Steam 公开资料读取成功，可将摘要合并到本次偏好。",
    )


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def serve_frontend() -> FileResponse:
    return FileResponse(FRONTEND_FILE)


@app.post("/api/steam/profile", response_model=SteamPreferenceSummary)
def parse_steam_profile(request: SteamProfileRequest) -> SteamPreferenceSummary:
    """读取无需 API Key 的 Steam 公开资料；私密资料会以状态响应。"""
    return read_public_steam_profile(request.steam_identifier)


@app.post("/api/preferences/submit")
def submit_preferences(preference: PreferenceSubmitRequest) -> dict[str, object]:
    """校验并返回推荐模块可直接使用的标准偏好对象。"""
    data = preference.model_dump(mode="json")
    return {"code": 200, "message": "偏好接收成功，已整理为推荐输入。", "data": data}
