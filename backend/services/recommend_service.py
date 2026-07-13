import json
from pathlib import Path
from typing import Any

from backend.config import Settings
from backend.models import GameCandidate, RecommendationItem, RecommendMeta, RecommendRequest, RecommendResponse
from backend.services.ai_service import call_ai_api
from backend.services.key_service import choose_api_key
from backend.services.prompt_service import PROMPT_VERSION, build_recommend_prompt


DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "games.json"


def generate_recommendations(
    request_data: RecommendRequest,
    user_api_key: str | None,
    settings: Settings,
) -> RecommendResponse:
    api_key_choice = choose_api_key(user_api_key, settings)
    candidate_games = request_data.candidate_games or load_default_games()

    if api_key_choice is None:
        if not settings.demo_mode_without_key:
            raise ValueError("未提供用户 API Key，后端也没有配置默认 API Key。")
        items = build_demo_recommendations(
            request_data.preferences,
            candidate_games,
            request_data.limit,
        )
        return RecommendResponse(
            data=items,
            meta=RecommendMeta(source="local-demo", demo_mode=True),
        )

    prompt = build_recommend_prompt(
        request_data.preferences,
        candidate_games,
        request_data.limit,
    )
    raw_content = call_ai_api(prompt, api_key_choice.key, settings)
    items = parse_ai_recommendations(raw_content, request_data.limit)

    return RecommendResponse(
        data=items,
        meta=RecommendMeta(
            source=api_key_choice.source,
            prompt_version=PROMPT_VERSION,
            model=settings.ai_model,
            used_user_key=api_key_choice.used_user_key,
            demo_mode=False,
        ),
    )


def load_default_games() -> list[GameCandidate]:
    if not DATA_FILE.exists():
        return []

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return [GameCandidate(**item) for item in data]


def parse_ai_recommendations(raw_content: str, limit: int) -> list[RecommendationItem]:
    cleaned = _strip_json_fence(raw_content)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("AI 返回内容不是合法 JSON。") from exc

    if isinstance(parsed, list):
        recommendations = parsed
    else:
        recommendations = parsed.get("recommendations") or parsed.get("data") or []

    if not isinstance(recommendations, list):
        raise ValueError("AI 返回 JSON 中缺少 recommendations 数组。")

    items: list[RecommendationItem] = []
    for item in recommendations[:limit]:
        if isinstance(item, dict):
            items.append(_normalize_recommendation(item))

    if not items:
        raise ValueError("AI 没有返回可用的推荐结果。")
    return items


def build_demo_recommendations(
    preferences: Any,
    candidate_games: list[GameCandidate],
    limit: int,
) -> list[RecommendationItem]:
    scored_games = sorted(
        candidate_games,
        key=lambda game: _score_game(game, preferences),
        reverse=True,
    )
    chosen_games = scored_games[:limit] if scored_games else []

    return [
        RecommendationItem(
            game_id=game.id,
            title=game.title,
            reason=_build_demo_reason(game, preferences),
            suitable_for=preferences.player_mode or "想要按偏好快速筛选游戏的玩家",
            platforms=game.platforms,
            tags=list(dict.fromkeys([*game.genres, *game.tags]))[:6],
            possible_drawbacks="这是无 API Key 时的本地演示结果，正式推荐建议接入 AI API 后生成。",
            similar_games=_similar_titles(game.title, candidate_games),
            match_score=min(100, max(60, _score_game(game, preferences))),
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


def _score_game(game: GameCandidate, preferences: Any) -> int:
    score = 60
    wanted_genres = {item.lower() for item in preferences.genres}
    wanted_platforms = {item.lower() for item in preferences.platforms}
    game_genres = {item.lower() for item in [*game.genres, *game.tags]}
    game_platforms = {item.lower() for item in game.platforms}

    score += 12 * len(wanted_genres & game_genres)
    score += 10 * len(wanted_platforms & game_platforms)

    extra = " ".join(
        str(value or "")
        for value in [
            preferences.player_mode,
            preferences.art_style,
            preferences.play_time,
            preferences.extra_requirements,
        ]
    ).lower()
    searchable = " ".join([game.description, *game.tags, *game.genres]).lower()
    for token in extra.replace("，", " ").replace(",", " ").split():
        if token and token in searchable:
            score += 3

    if game.score:
        score += int(game.score)
    return score


def _build_demo_reason(game: GameCandidate, preferences: Any) -> str:
    matched = []
    if preferences.genres:
        matched.append(f"类型偏好：{', '.join(preferences.genres)}")
    if preferences.platforms:
        matched.append(f"平台偏好：{', '.join(preferences.platforms)}")
    if preferences.art_style:
        matched.append(f"画风偏好：{preferences.art_style}")

    base = "、".join(matched) if matched else "你的综合偏好"
    return f"{game.title} 与{base}比较匹配，适合作为本轮推荐候选。"


def _similar_titles(title: str, games: list[GameCandidate]) -> list[str]:
    return [game.title for game in games if game.title != title][:3]

