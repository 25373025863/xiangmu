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
from backend.src.services.catalogue_service import LOCAL_STEAM_APP_IDS, catalogue_service
from backend.src.services.game_service import GameService
from backend.src.services.key_service import choose_provider_config
from backend.src.services.prompt_service import PROMPT_VERSION, build_recommend_prompt


RECOMMENDATION_CATALOGUE_PAGE_SIZE = 25
MAX_RECOMMENDATION_CANDIDATES = 35


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
    if request_data.candidate_games:
        candidate_games = prepare_candidate_pool(
            request_data.candidate_games,
            request_data.preferences,
        )
    else:
        candidate_games = load_recommendation_candidates(
            request_data.preferences,
            request_data.limit,
        )
    target_count = min(request_data.limit, len(candidate_games))

    if provider is None:
        recommendations = build_demo_recommendations(
            request_data.preferences,
            candidate_games,
            target_count,
        )
        if not settings.demo_mode_without_key:
            raise ValueError("未提供用户 API Key，后端也没有配置默认 API Key。")
        return RecommendResponse(
            data=recommendations,
            meta=RecommendMeta(
                source="local-demo",
                demo_mode=True,
                requested_count=request_data.limit,
                returned_count=len(recommendations),
                candidate_count=len(candidate_games),
            ),
        )

    if target_count == 0:
        return RecommendResponse(
            data=[],
            meta=RecommendMeta(
                source=provider.source,
                model=provider.model,
                used_user_key=provider.used_user_key,
                requested_count=request_data.limit,
                returned_count=0,
                candidate_count=0,
            ),
        )

    prompt = build_recommend_prompt(
        request_data.preferences,
        candidate_games,
        target_count,
    )
    raw_content = call_ai_api(prompt, provider, settings.ai_timeout_seconds)
    ai_recommendations = parse_ai_recommendations(raw_content, target_count)
    recommendations = complete_ai_recommendations(
        ai_recommendations,
        request_data.preferences,
        candidate_games,
        target_count,
    )
    return RecommendResponse(
        data=recommendations,
        meta=RecommendMeta(
            source=provider.source,
            prompt_version=PROMPT_VERSION,
            model=provider.model,
            used_user_key=provider.used_user_key,
            requested_count=request_data.limit,
            returned_count=len(recommendations),
            candidate_count=len(candidate_games),
        ),
    )


def load_default_games() -> list[GameCandidate]:
    candidates: list[GameCandidate] = []
    for game in GameService().list_games():
        data = dict(game)
        game_id = str(data.get("id", ""))
        app_id = data.get("steam_app_id") or LOCAL_STEAM_APP_IDS.get(game_id)
        data["steam_app_id"] = app_id
        data["source"] = "local"
        if app_id:
            data.setdefault(
                "cover_url",
                f"https://cdn.cloudflare.steamstatic.com/steam/apps/{app_id}/header.jpg",
            )
            data.setdefault(
                "store_url",
                f"https://store.steampowered.com/app/{app_id}/",
            )
        candidates.append(GameCandidate(**data))
    return candidates


def load_recommendation_candidates(
    preferences: Any,
    limit: int,
) -> list[GameCandidate]:
    local_candidates = load_default_games()
    remote_candidates: list[GameCandidate] = []
    first_page: dict[str, Any] | None = None

    try:
        first_page = catalogue_service.list_games(
            page=1,
            size=RECOMMENDATION_CATALOGUE_PAGE_SIZE,
            sort="topsellers",
        )
        remote_candidates.extend(_catalogue_candidates(first_page))
    except (OSError, RuntimeError, TypeError, ValueError):
        return prepare_candidate_pool(local_candidates, preferences)

    prepared = prepare_candidate_pool(
        [*local_candidates, *remote_candidates],
        preferences,
    )
    variety_target = min(MAX_RECOMMENDATION_CANDIDATES, max(limit * 3, limit))
    if (
        first_page
        and first_page.get("source") == "steam"
        and not first_page.get("degraded")
        and first_page.get("has_more")
        and len(prepared) < variety_target
    ):
        try:
            second_page = catalogue_service.list_games(
                page=2,
                size=RECOMMENDATION_CATALOGUE_PAGE_SIZE,
                sort="topsellers",
            )
            remote_candidates.extend(_catalogue_candidates(second_page))
            prepared = prepare_candidate_pool(
                [*local_candidates, *remote_candidates],
                preferences,
            )
        except (OSError, RuntimeError, TypeError, ValueError):
            pass
    return prepared


def prepare_candidate_pool(
    candidate_games: list[GameCandidate],
    preferences: Any,
) -> list[GameCandidate]:
    steam_summary = _public_steam_library(preferences)
    prepared: list[GameCandidate] = []
    seen_app_ids: set[int] = set()
    seen_titles: set[str] = set()

    for game in candidate_games:
        if _is_owned_steam_game(game, steam_summary):
            continue
        title_key = _normalised_title(game.title)
        if not title_key:
            continue
        if game.steam_app_id is not None and game.steam_app_id in seen_app_ids:
            continue
        if title_key in seen_titles:
            continue
        if game.steam_app_id is not None:
            seen_app_ids.add(game.steam_app_id)
        seen_titles.add(title_key)
        prepared.append(game)

    return sorted(
        prepared,
        key=lambda game: _score_game(game, preferences, steam_summary),
        reverse=True,
    )[:MAX_RECOMMENDATION_CANDIDATES]


def _catalogue_candidates(data: dict[str, Any]) -> list[GameCandidate]:
    if data.get("source") != "steam" or data.get("degraded"):
        return []
    candidates: list[GameCandidate] = []
    for item in data.get("items") or []:
        if not isinstance(item, dict):
            continue
        try:
            app_id = int(item.get("steam_app_id") or 0)
        except (TypeError, ValueError):
            continue
        title = str(item.get("title") or "").strip()
        if app_id <= 0 or not title:
            continue
        review_score = item.get("review_score")
        try:
            score = float(review_score) / 10 if review_score is not None else None
        except (TypeError, ValueError):
            score = None
        platforms = [
            "PC" if str(platform).casefold() == "windows" else str(platform)
            for platform in item.get("platforms") or []
            if platform
        ]
        review_label = str(item.get("review_label") or "").strip()
        release_date = str(item.get("release_date") or "").strip()
        description_parts = [part for part in (review_label, release_date) if part]
        candidates.append(
            GameCandidate(
                id=f"steam-{app_id}",
                steam_app_id=app_id,
                title=title,
                platforms=platforms,
                price=item.get("price"),
                score=score,
                description="；".join(description_parts),
                cover_url=str(item.get("cover_url") or ""),
                store_url=f"https://store.steampowered.com/app/{app_id}/",
                release_date=release_date,
                review_label=review_label,
                source="steam",
            )
        )
    return candidates


def parse_ai_recommendations(raw_content: str, limit: int) -> list[RecommendationItem]:
    cleaned = _strip_json_fence(raw_content)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("AI 返回内容不是合法 JSON。") from exc
    recommendations = parsed if isinstance(parsed, list) else parsed.get("recommendations") or parsed.get("data") or []
    if not isinstance(recommendations, list):
        raise ValueError("AI 返回 JSON 中缺少 recommendations 数组。")
    items: list[RecommendationItem] = []
    for item in recommendations:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("name")
        if not isinstance(title, str) or not title.strip():
            continue
        items.append(_normalize_recommendation(item))
        if len(items) == limit:
            break
    if not items:
        raise ValueError("AI 没有返回可用的推荐结果。")
    return items


def complete_ai_recommendations(
    ai_items: list[RecommendationItem],
    preferences: Any,
    candidate_games: list[GameCandidate],
    target_count: int,
) -> list[RecommendationItem]:
    completed: list[RecommendationItem] = []
    seen: set[str] = set()

    for item in ai_items:
        candidate = _find_candidate(item, candidate_games)
        if candidate is None:
            continue
        identity = _recommendation_identity(candidate)
        if identity in seen:
            continue
        seen.add(identity)
        completed.append(_enrich_recommendation(item, candidate))
        if len(completed) == target_count:
            return completed

    fallback_items = build_demo_recommendations(
        preferences,
        candidate_games,
        target_count,
    )
    for item in fallback_items:
        candidate = _find_candidate(item, candidate_games)
        if candidate is None:
            continue
        identity = _recommendation_identity(candidate)
        if identity in seen:
            continue
        seen.add(identity)
        completed.append(
            item.model_copy(
                update={
                    "possible_drawbacks": (
                        "该条目由候选排序自动补足，部分次要偏好请在商店页面进一步确认。"
                    )
                }
            )
        )
        if len(completed) == target_count:
            break
    return completed


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
            steam_app_id=game.steam_app_id,
            price=game.price,
            cover_url=game.cover_url,
            store_url=game.store_url,
            source=game.source or "local",
        )
        for game in chosen_games
    ]


def _normalize_recommendation(item: dict) -> RecommendationItem:
    return RecommendationItem(
        game_id=item.get("game_id") or item.get("id"),
        steam_app_id=item.get("steam_app_id") or item.get("app_id"),
        title=str(item.get("title") or item.get("name")),
        reason=str(item.get("reason") or item.get("recommend_reason") or "符合用户偏好。"),
        suitable_for=str(item.get("suitable_for") or item.get("player_type") or "目标玩家"),
        platforms=_to_string_list(item.get("platforms")),
        tags=_to_string_list(item.get("tags") or item.get("match_tags")),
        possible_drawbacks=str(item.get("possible_drawbacks") or item.get("drawbacks") or ""),
        similar_games=_to_string_list(item.get("similar_games")),
        match_score=_to_score(item.get("match_score") or item.get("score")),
        price=item.get("price"),
        cover_url=str(item.get("cover_url") or ""),
        store_url=str(item.get("store_url") or ""),
        source=str(item.get("source") or ""),
    )


def _find_candidate(
    item: RecommendationItem,
    candidate_games: list[GameCandidate],
) -> GameCandidate | None:
    item_id = str(item.game_id).strip().casefold() if item.game_id is not None else ""
    title = _normalised_title(item.title)
    for candidate in candidate_games:
        candidate_id = (
            str(candidate.id).strip().casefold() if candidate.id is not None else ""
        )
        if item_id and candidate_id == item_id:
            return candidate
        if item.steam_app_id and candidate.steam_app_id == item.steam_app_id:
            return candidate
    if title:
        return next(
            (
                candidate
                for candidate in candidate_games
                if _normalised_title(candidate.title) == title
            ),
            None,
        )
    return None


def _recommendation_identity(candidate: GameCandidate) -> str:
    if candidate.steam_app_id is not None:
        return f"steam:{candidate.steam_app_id}"
    return f"title:{_normalised_title(candidate.title)}"


def _enrich_recommendation(
    item: RecommendationItem,
    candidate: GameCandidate,
) -> RecommendationItem:
    return item.model_copy(
        update={
            "game_id": candidate.id,
            "steam_app_id": candidate.steam_app_id,
            "title": candidate.title,
            "platforms": item.platforms or candidate.platforms,
            "tags": item.tags or list(dict.fromkeys([*candidate.genres, *candidate.tags])),
            "price": candidate.price,
            "cover_url": candidate.cover_url,
            "store_url": candidate.store_url,
            "source": candidate.source or "local",
        }
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
