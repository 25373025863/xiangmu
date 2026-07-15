import json
import unicodedata
from typing import Any

from backend.src.config.settings import Settings
from backend.src.models.schemas import (
    GameCandidate,
    RecommendationItem,
    RecommendMeta,
    RecommendRequest,
    RecommendResponse,
)
from backend.src.services.ai_service import call_ai_api
from backend.src.services.game_service import GameService
from backend.src.services.key_service import choose_provider_config
from backend.src.services.prompt_service import PROMPT_VERSION, build_recommend_prompt


def generate_recommendations(
    request_data: RecommendRequest,
    user_api_key: str | None,
    settings: Settings,
) -> RecommendResponse:
    provider = choose_provider_config(
        user_api_key,
        settings,
        api_base_url=request_data.api_base_url,
        model=request_data.model,
    )
    candidate_games = request_data.candidate_games or load_default_games()
    if provider is None:
        if not settings.demo_mode_without_key:
            raise ValueError("未提供用户 API Key，后端也没有配置默认 API Key。")
        return RecommendResponse(
            data=build_demo_recommendations(
                request_data.preferences, candidate_games, request_data.limit
            ),
            meta=RecommendMeta(source="local-demo", demo_mode=True),
        )

    prompt = build_recommend_prompt(
        request_data.preferences, candidate_games, request_data.limit
    )
    raw_content = call_ai_api(prompt, provider, settings.ai_timeout_seconds)
    return RecommendResponse(
        data=parse_ai_recommendations(raw_content, request_data.limit),
        meta=RecommendMeta(
            source=provider.source,
            prompt_version=PROMPT_VERSION,
            model=provider.model,
            used_user_key=provider.used_user_key,
        ),
    )


def load_default_games() -> list[GameCandidate]:
    return [GameCandidate(**game) for game in GameService().list_games()]


def parse_ai_recommendations(raw_content: str, limit: int) -> list[RecommendationItem]:
    cleaned = _strip_json_fence(raw_content)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("AI 返回内容不是合法 JSON。") from exc
    recommendations = parsed if isinstance(parsed, list) else parsed.get("recommendations") or parsed.get("data") or []
    if not isinstance(recommendations, list):
        raise ValueError("AI 返回 JSON 中缺少 recommendations 数组。")
    items = [_normalize_recommendation(item) for item in recommendations[:limit] if isinstance(item, dict)]
    if not items:
        raise ValueError("AI 没有返回可用的推荐结果。")
    return items


def build_demo_recommendations(
    preferences: Any,
    candidate_games: list[GameCandidate],
    limit: int,
) -> list[RecommendationItem]:
    steam_summary = _public_steam_library(preferences)
    available_games = [
        game for game in candidate_games if not _is_owned_steam_game(game, steam_summary)
    ]
    chosen_games = sorted(
        available_games,
        key=lambda game: _score_game(game, preferences, steam_summary),
        reverse=True,
    )[:limit]
    return [
        RecommendationItem(
            game_id=game.id,
            title=game.title,
            reason=_build_demo_reason(game, preferences, steam_summary),
            suitable_for=preferences.player_mode or "想要按偏好快速筛选游戏的玩家",
            platforms=game.platforms,
            tags=list(dict.fromkeys([*game.genres, *game.tags]))[:6],
            possible_drawbacks="当前为无 API Key 的本地演示结果。",
            similar_games=[item.title for item in available_games if item.title != game.title][:3],
            match_score=min(100, max(60, _score_game(game, preferences, steam_summary))),
        )
        for game in chosen_games
    ]


def _normalize_recommendation(item: dict) -> RecommendationItem:
    return RecommendationItem(
        game_id=item.get("game_id") or item.get("id"),
        title=str(item.get("title") or item.get("name") or "未命名游戏"),
        reason=str(item.get("reason") or item.get("recommend_reason") or "符合用户偏好。"),
        suitable_for=str(item.get("suitable_for") or item.get("player_type") or "目标玩家"),
        platforms=_to_string_list(item.get("platforms")),
        tags=_to_string_list(item.get("tags") or item.get("match_tags")),
        possible_drawbacks=str(item.get("possible_drawbacks") or item.get("drawbacks") or ""),
        similar_games=_to_string_list(item.get("similar_games")),
        match_score=_to_score(item.get("match_score") or item.get("score")),
    )


def _strip_json_fence(content: str) -> str:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
        cleaned = cleaned.removesuffix("```").strip()
    return cleaned


def _to_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def _to_score(value: Any) -> float:
    try:
        return max(0, min(100, float(value)))
    except (TypeError, ValueError):
        return 0


def _public_steam_library(preferences: Any) -> dict[str, Any] | None:
    summary = getattr(preferences, "steam_summary", None)
    if not isinstance(summary, dict) or summary.get("visibility") != "public":
        return None
    try:
        game_count = int(summary.get("game_count") or 0)
    except (TypeError, ValueError):
        return None
    return summary if game_count > 0 else None


def _string_values(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        item.strip()
        for item in value
        if isinstance(item, str) and item.strip()
    ]


def _normalised_values(value: Any) -> set[str]:
    return {item.casefold() for item in _string_values(value)}


def _normalised_title(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _owned_steam_app_ids(summary: dict[str, Any] | None) -> set[int]:
    if not summary or not isinstance(summary.get("owned_game_app_ids"), list):
        return set()
    app_ids: set[int] = set()
    for value in summary["owned_game_app_ids"]:
        try:
            app_id = int(value)
        except (TypeError, ValueError):
            continue
        if app_id > 0:
            app_ids.add(app_id)
    return app_ids


def _owned_steam_titles(summary: dict[str, Any] | None) -> set[str]:
    if not summary or not isinstance(summary.get("top_games"), list):
        return set()
    titles = {
        _normalised_title(game.get("name"))
        for game in summary["top_games"]
        if isinstance(game, dict)
    }
    return {title for title in titles if title}


def _is_owned_steam_game(
    game: GameCandidate,
    steam_summary: dict[str, Any] | None,
) -> bool:
    if not steam_summary:
        return False
    if game.steam_app_id is not None and game.steam_app_id in _owned_steam_app_ids(steam_summary):
        return True
    return _normalised_title(game.title) in _owned_steam_titles(steam_summary)


def _score_game(
    game: GameCandidate,
    preferences: Any,
    steam_summary: dict[str, Any] | None = None,
) -> int:
    score = 60
    wanted_genres = _normalised_values(preferences.genres)
    wanted_platforms = _normalised_values(preferences.platforms)
    game_genres = _normalised_values([*game.genres, *game.tags])
    game_platforms = _normalised_values(game.platforms)
    score += 12 * len(wanted_genres & game_genres)
    score += 10 * len(wanted_platforms & game_platforms)
    if steam_summary:
        inferred_genres = _normalised_values(steam_summary.get("inferred_game_types")) - wanted_genres
        suggested_platforms = _normalised_values(steam_summary.get("suggested_platforms")) - wanted_platforms
        score += 6 * len(inferred_genres & game_genres)
        score += 5 * len(suggested_platforms & game_platforms)
    if game.score:
        score += int(game.score)
    return score


def _build_demo_reason(
    game: GameCandidate,
    preferences: Any,
    steam_summary: dict[str, Any] | None = None,
) -> str:
    matched = []
    if preferences.genres:
        matched.append(f"类型偏好：{', '.join(preferences.genres)}")
    if preferences.platforms:
        matched.append(f"平台偏好：{', '.join(preferences.platforms)}")
    if steam_summary:
        inferred_genres = [
            item
            for item in _string_values(steam_summary.get("inferred_game_types"))
            if item.casefold() not in _normalised_values(preferences.genres)
        ]
        suggested_platforms = [
            item
            for item in _string_values(steam_summary.get("suggested_platforms"))
            if item.casefold() not in _normalised_values(preferences.platforms)
        ]
        steam_signals = [*inferred_genres, *suggested_platforms]
        if steam_signals:
            matched.append(f"Steam 游戏库推断：{', '.join(steam_signals)}")
    base = "、".join(matched) if matched else "你的综合偏好"
    return f"{game.title} 与{base}比较匹配，适合作为本轮推荐候选。"
