"""GAME//PULSE 用户偏好与 Steam 公开资料接口。"""

from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlencode, urlparse
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


STEAM_COMMUNITY_HOSTS = {"steamcommunity.com", "www.steamcommunity.com"}
STEAM_TIMEOUT_SECONDS = 12


@dataclass(frozen=True)
class HttpPayload:
    """The response metadata needed to distinguish XML from a login redirect."""

    body: bytes
    final_url: str
    content_type: str


@dataclass(frozen=True)
class SteamLibrary:
    owned_games: list[dict[str, object]]
    recent_games: list[dict[str, object]]
    library_visible: bool


def parse_steam_identifier(raw: str) -> tuple[str, str]:
    """Return a canonical Steam Community path segment and identifier.

    Accepts SteamID64, Steam2 IDs, profile/vanity URLs (including links to a
    subpage such as ``/games``), and a bare vanity name. Parsing the URL rather
    than searching it prevents unrelated domains from being accepted.
    """
    value = raw.strip()
    if re.fullmatch(r"\d{17}", value):
        return "profiles", value

    steam2_match = re.fullmatch(r"STEAM_[0-5]:[01]:\d+", value, re.IGNORECASE)
    if steam2_match:
        _, parity, account = value.upper().split(":")
        return "profiles", str(76561197960265728 + int(account) * 2 + int(parity))

    steam3_match = re.fullmatch(r"\[U:1:(\d+)\]", value, re.IGNORECASE)
    if steam3_match:
        return "profiles", str(76561197960265728 + int(steam3_match.group(1)))

    candidate = value
    if candidate.lower().startswith(("steamcommunity.com/", "www.steamcommunity.com/")):
        candidate = f"https://{candidate}"
    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()
    if parsed.scheme and host:
        if host not in STEAM_COMMUNITY_HOSTS:
            raise ValueError("请输入 steamcommunity.com 的个人资料链接或有效 SteamID")
        path_parts = [unquote(part) for part in parsed.path.split("/") if part]
        if len(path_parts) >= 2 and path_parts[0].lower() in {"profiles", "id"}:
            segment = path_parts[0].lower()
            identifier = path_parts[1]
            if segment == "profiles" and re.fullmatch(r"\d{17}", identifier):
                return segment, identifier
            if segment == "id" and re.fullmatch(r"[A-Za-z0-9_-]{2,100}", identifier):
                return segment, identifier
        raise ValueError("Steam 个人资料链接应包含 /profiles/<SteamID64> 或 /id/<自定义 ID>")

    if re.fullmatch(r"[A-Za-z0-9_-]{2,100}", value):
        return "id", value
    raise ValueError("请输入有效的 SteamID、SteamID64、个人资料链接或自定义 URL")


def fetch_response(url: str) -> HttpPayload:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; GAME-PULSE/2.0; public-profile reader)",
            "Accept": "application/json, application/xml, text/xml, text/html;q=0.9, */*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8",
        },
    )
    with urlopen(request, timeout=STEAM_TIMEOUT_SECONDS) as response:
        content_type = response.headers.get_content_type()
        return HttpPayload(response.read(), response.geturl(), content_type)


def fetch(url: str) -> bytes:
    """Compatibility wrapper for callers that only need the response body."""
    return fetch_response(url).body


def fetch_json(url: str) -> dict[str, object]:
    payload = json.loads(fetch(url).decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Steam API returned an unexpected JSON payload")
    return payload


def text(element: ET.Element | None, tag: str) -> str | None:
    node = element.find(tag) if element is not None else None
    return node.text.strip() if node is not None and node.text else None


def game_record(
    app_id: int | str | None,
    name: str | None,
    minutes: int | float | str | None,
) -> dict[str, object] | None:
    if not isinstance(name, str) or not name.strip():
        return None
    try:
        normalised_app_id = int(app_id) if app_id is not None else None
    except (TypeError, ValueError):
        normalised_app_id = None
    try:
        hours_played = round(float(minutes or 0) / 60, 1)
    except (TypeError, ValueError):
        hours_played = 0
    return {
        "app_id": normalised_app_id,
        "name": name.strip(),
        "hours_played": hours_played,
    }


def _normalise_web_api_games(
    response: dict[str, object],
    playtime_field: str,
) -> list[dict[str, object]]:
    games = response.get("games", [])
    if not isinstance(games, list):
        return []
    records = [
        game_record(game.get("appid"), game.get("name"), game.get(playtime_field, 0))
        for game in games
        if isinstance(game, dict)
    ]
    return [record for record in records if record]


def read_steam_web_api_library(steam_id64: str) -> SteamLibrary | None:
    """Read the official owned/recent-game endpoints when a server key exists.

    A successful owned-games response with ``game_count`` is meaningful even
    when the account owns zero games. An empty ``response`` instead signals
    that Steam did not expose the library, usually because Game details are
    private.
    """
    api_key = os.getenv("STEAM_API_KEY")
    if not api_key:
        return None

    owned_query = urlencode({
        "key": api_key, "steamid": steam_id64, "include_appinfo": "1",
        "include_played_free_games": "1",
    })
    recent_query = urlencode({"key": api_key, "steamid": steam_id64, "format": "json"})
    owned_payload = fetch_json(
        f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?{owned_query}"
    )
    owned_response = owned_payload.get("response", {})
    if not isinstance(owned_response, dict):
        raise ValueError("Steam owned-games response is malformed")

    recent_games: list[dict[str, object]] = []
    try:
        recent_payload = fetch_json(
            f"https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?{recent_query}"
        )
        recent_response = recent_payload.get("response", {})
        if isinstance(recent_response, dict):
            recent_games = _normalise_web_api_games(recent_response, "playtime_2weeks")
    except (HTTPError, URLError, OSError, ValueError, json.JSONDecodeError):
        # Recent games are supplementary. Keep a valid owned-games result.
        recent_games = []

    return SteamLibrary(
        owned_games=_normalise_web_api_games(owned_response, "playtime_forever"),
        recent_games=recent_games,
        library_visible="game_count" in owned_response or "games" in owned_response,
    )


def resolve_vanity_url(vanity_name: str) -> str | None:
    """Resolve an /id URL if the public profile XML endpoint is unavailable."""
    api_key = os.getenv("STEAM_API_KEY")
    if not api_key:
        return None
    query = urlencode({"key": api_key, "vanityurl": vanity_name})
    payload = fetch_json(
        f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?{query}"
    )
    response = payload.get("response", {})
    if not isinstance(response, dict) or response.get("success") != 1:
        return None
    steam_id64 = response.get("steamid")
    return steam_id64 if isinstance(steam_id64, str) and re.fullmatch(r"\d{17}", steam_id64) else None


def is_login_redirect(payload: HttpPayload) -> bool:
    final_path = urlparse(payload.final_url).path.lower()
    if final_path.startswith("/login"):
        return True
    body_start = payload.body[:2048].lower()
    return b"steamcommunity.com/login" in body_start or b"id=\"login_form\"" in body_start


def parse_public_library_xml(payload: HttpPayload) -> tuple[list[dict[str, object]], list[GameType], bool] | None:
    """Parse the legacy game-list XML only when Steam really returned XML."""
    if is_login_redirect(payload):
        return None
    try:
        root = ET.fromstring(payload.body)
    except (ET.ParseError, ValueError):
        return None
    if root.tag.lower() not in {"gameslist", "games"}:
        return None

    genres: Counter[str] = Counter()
    owned_games: list[dict[str, object]] = []
    multiplayer = False
    for game in root.findall(".//game"):
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

    return owned_games, [genre for genre, _ in genres.most_common(3)], multiplayer


def _profile_summary(
    *,
    steam_id64: str,
    profile_name: str | None,
    profile_url: str,
    owned_games: list[dict[str, object]] | None = None,
    recent_games: list[dict[str, object]] | None = None,
    inferred_game_types: list[GameType] | None = None,
    suggested_player_mode: PlayerMode | None = None,
    data_source: Literal["steam_web_api", "public_xml", "profile_only"] = "profile_only",
    message: str,
) -> SteamPreferenceSummary:
    owned = sorted(owned_games or [], key=lambda item: float(item["hours_played"]), reverse=True)
    recent = sorted(recent_games or [], key=lambda item: float(item["hours_played"]), reverse=True)
    return SteamPreferenceSummary(
        steam_id64=steam_id64,
        profile_name=profile_name,
        profile_url=profile_url,
        visibility="public",
        game_count=len(owned),
        total_playtime_hours=round(sum(float(game["hours_played"]) for game in owned), 1),
        top_games=owned[:5],
        recent_games=recent[:5],
        owned_game_app_ids=[int(game["app_id"]) for game in owned if isinstance(game.get("app_id"), int)],
        inferred_game_types=inferred_game_types or [],
        suggested_player_mode=suggested_player_mode,
        data_source=data_source,
        message=message,
    )


def _try_web_api_profile_fallback(
    *,
    segment: str,
    identifier: str,
    profile_url: str,
) -> SteamPreferenceSummary | None:
    """Use the official API when Steam Community profile XML is unavailable."""
    try:
        steam_id64 = identifier if segment == "profiles" else resolve_vanity_url(identifier)
        if not steam_id64:
            return None
        api_library = read_steam_web_api_library(steam_id64)
    except (HTTPError, URLError, OSError, ValueError, json.JSONDecodeError):
        return None

    if not api_library or not api_library.library_visible:
        return None
    return _profile_summary(
        steam_id64=steam_id64,
        profile_name=None,
        profile_url=profile_url,
        owned_games=api_library.owned_games,
        recent_games=api_library.recent_games,
        data_source="steam_web_api",
        message="已通过 Steam Web API 读取公开游戏库。",
    )


def read_public_steam_profile(raw_identifier: str) -> SteamPreferenceSummary:
    try:
        segment, identifier = parse_steam_identifier(raw_identifier)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    profile_url = f"https://steamcommunity.com/{segment}/{quote(identifier, safe='')}/"
    try:
        profile_payload = fetch_response(f"{profile_url}?xml=1")
        if is_login_redirect(profile_payload):
            raise ET.ParseError("Steam redirected the profile request to login")
        root = ET.fromstring(profile_payload.body)
        if root.tag.lower() != "profile":
            raise ET.ParseError("Steam did not return a profile XML document")
    except HTTPError as error:
        if error.code == 404:
            return SteamPreferenceSummary(steam_id64=identifier if segment == "profiles" else "", visibility="not_found", profile_url=profile_url, message="未找到该 Steam 个人资料。")
        api_summary = _try_web_api_profile_fallback(
            segment=segment,
            identifier=identifier,
            profile_url=profile_url,
        )
        if api_summary:
            return api_summary
        return SteamPreferenceSummary(steam_id64=identifier if segment == "profiles" else "", visibility="unavailable", profile_url=profile_url, message="Steam 暂时无法响应，请稍后重试。")
    except (URLError, OSError, ET.ParseError, TimeoutError):
        api_summary = _try_web_api_profile_fallback(
            segment=segment,
            identifier=identifier,
            profile_url=profile_url,
        )
        if api_summary:
            return api_summary
        return SteamPreferenceSummary(steam_id64=identifier if segment == "profiles" else "", visibility="unavailable", profile_url=profile_url, message="无法连接 Steam，请检查网络后重试。")

    steam_id64 = text(root, "steamID64") or (identifier if segment == "profiles" else "")
    profile_name = text(root, "steamID")
    privacy = text(root, "privacyState")
    if privacy and privacy.lower() != "public":
        return SteamPreferenceSummary(steam_id64=steam_id64, profile_name=profile_name, profile_url=profile_url, visibility="private", message="该 Steam 资料或游戏库不可见，请将资料和游戏详情设为公开。")

    try:
        api_library = read_steam_web_api_library(steam_id64)
    except (HTTPError, URLError, OSError, ValueError, json.JSONDecodeError):
        api_library = None
    if api_library and api_library.library_visible:
        return _profile_summary(
            steam_id64=steam_id64,
            profile_name=profile_name,
            profile_url=profile_url,
            owned_games=api_library.owned_games,
            recent_games=api_library.recent_games,
            data_source="steam_web_api",
            message="Steam 公开游戏库读取成功，可将摘要合并到本次偏好。",
        )

    # Steam has begun redirecting this legacy endpoint to login for many public
    # profiles. Keep it as a compatibility fallback, but never parse that HTML
    # response as an empty XML game list.
    games_url = f"{profile_url}games/?tab=all&xml=1"
    try:
        legacy_library = parse_public_library_xml(fetch_response(games_url))
    except (HTTPError, URLError, OSError, TimeoutError):
        legacy_library = None
    if legacy_library:
        owned_games, inferred_types, multiplayer = legacy_library
        return _profile_summary(
            steam_id64=steam_id64,
            profile_name=profile_name,
            profile_url=profile_url,
            owned_games=owned_games,
            inferred_game_types=inferred_types,
            suggested_player_mode="在线多人" if multiplayer else "单人",
            data_source="public_xml",
            message="Steam 公开游戏库读取成功，可将摘要合并到本次偏好。",
        )

    if api_library and not api_library.library_visible:
        library_message = "Steam 资料可读，但“游戏详情”当前未公开；请将其设为公开后重试。"
    elif os.getenv("STEAM_API_KEY"):
        library_message = "Steam 资料可读，但游戏库暂时不可读取；请确认“游戏详情”已公开后重试。"
    else:
        library_message = "Steam 资料可读，但 Steam 已限制此公开游戏库入口；请配置服务器 STEAM_API_KEY 后重试，或继续手动填写偏好。"
    return _profile_summary(
        steam_id64=steam_id64,
        profile_name=profile_name,
        profile_url=profile_url,
        data_source="profile_only",
        message=library_message,
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
