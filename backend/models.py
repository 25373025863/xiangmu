from typing import Any

from pydantic import BaseModel, Field


class GameCandidate(BaseModel):
    id: str | int | None = None
    title: str
    genres: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    price: str | float | int | None = None
    score: float | None = None
    description: str = ""


class PreferenceInput(BaseModel):
    genres: list[str] = Field(default_factory=list, description="喜欢的游戏类型")
    platforms: list[str] = Field(default_factory=list, description="使用的平台")
    budget: str | float | int | None = Field(default=None, description="预算")
    player_mode: str | None = Field(default=None, description="单人/多人")
    art_style: str | None = Field(default=None, description="画风偏好")
    play_time: str | None = Field(default=None, description="游玩时长偏好")
    chinese_support: bool | None = Field(default=None, description="是否需要中文")
    extra_requirements: str | None = Field(default=None, description="其他需求")


class RecommendRequest(BaseModel):
    preferences: PreferenceInput
    candidate_games: list[GameCandidate] = Field(
        default_factory=list,
        description="可选候选游戏；整合成员3模块后可从游戏库传入",
    )
    limit: int = Field(default=5, ge=1, le=10)


class RecommendationItem(BaseModel):
    game_id: str | int | None = None
    title: str
    reason: str
    suitable_for: str
    platforms: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    possible_drawbacks: str = ""
    similar_games: list[str] = Field(default_factory=list)
    match_score: float = Field(default=0, ge=0, le=100)


class RecommendMeta(BaseModel):
    source: str
    prompt_version: str = "member4-v1"
    model: str | None = None
    used_user_key: bool = False
    demo_mode: bool = False


class RecommendResponse(BaseModel):
    success: bool = True
    data: list[RecommendationItem]
    meta: RecommendMeta


class KeyCheckRequest(BaseModel):
    api_key: str | None = Field(default=None, alias="apiKey")

    model_config = {"populate_by_name": True}


class KeyCheckResponse(BaseModel):
    success: bool = True
    data: dict[str, Any]


class GameDetail(BaseModel):
    id: str
    title: str
    cover: str | None = None
    genres: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    price: str | float | int | None = None
    score: float | None = None
    developer: str | None = None
    release_date: str | None = None
    description: str = ""
    suitable_for: list[str] = Field(default_factory=list)
    purchase_url: str | None = None


class GameDetailResponse(BaseModel):
    success: bool = True
    data: GameDetail

