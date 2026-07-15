import json

from backend.src.models.schemas import GameCandidate, PreferenceInput

PROMPT_VERSION = "member4-v1"
SYSTEM_PROMPT = """你是一个游戏推荐助手。你只能根据用户偏好和候选游戏生成推荐。
请用简洁中文回答，并且必须返回合法 JSON，不要返回 Markdown。"""


def build_recommend_prompt(
    preferences: PreferenceInput,
    candidate_games: list[GameCandidate],
    limit: int,
) -> str:
    schema = {
        "recommendations": [
            {
                "game_id": "候选游戏 id，没有则为 null",
                "title": "游戏名称",
                "reason": "推荐理由",
                "suitable_for": "适合的玩家类型",
                "platforms": ["平台"],
                "tags": ["匹配标签"],
                "possible_drawbacks": "可能缺点",
                "similar_games": ["相似游戏"],
                "match_score": "0 到 100 的数字",
            }
        ]
    }
    return "\n".join(
        [
            "请根据以下用户偏好和候选游戏生成推荐结果。",
            f"最多推荐 {limit} 个游戏，优先选择候选游戏中真实存在的条目。",
            "用户偏好 JSON：",
            json.dumps(preferences.model_dump(exclude_none=True), ensure_ascii=False),
            "候选游戏 JSON：",
            json.dumps(
                [game.model_dump(exclude_none=True) for game in candidate_games],
                ensure_ascii=False,
            ),
            "返回 JSON 格式：",
            json.dumps(schema, ensure_ascii=False),
        ]
    )
