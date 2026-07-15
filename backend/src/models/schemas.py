from typing import Any

from pydantic import AliasChoices, BaseModel, Field, field_validator


class GameCandidate(BaseModel):
    id: str | int | None = None
    steam_app_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("steam_app_id", "app_id"),
    )
    title: str
    genres: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    price: str | float | int | None = None
    score: float | None = None
    description: str = ""


class PreferenceInput(BaseModel):
    genres: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("genres", "game_types"),
    )
    platforms: list[str] = Field(default_factory=list)
    budget: str | float | int | None = None
    player_mode: str | None = None
    art_style: str | None = Field(
        default=None,
        validation_alias=AliasChoices("art_style", "art_styles"),
    )
    play_time: str | None = Field(
        default=None,
        validation_alias=AliasChoices("play_time", "duration_preference"),
    )
    chinese_support: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("chinese_support", "chinese_required"),
    )
    extra_requirements: str | None = Field(
        default=None,
        validation_alias=AliasChoices("extra_requirements", "notes"),
        max_length=1000,
    )
    steam_summary: dict[str, Any] | None = None

    @field_validator("genres", "platforms")
    @classmethod
    def unique_values(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("选项不能重复")
        return cleaned


class RecommendRequest(BaseModel):
    preferences: PreferenceInput
    candidate_games: list[GameCandidate] = Field(default_factory=list)
    limit: int = Field(default=5, ge=1, le=10)
    api_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("api_base_url", "apiBaseUrl"),
    )
    model: str | None = None

    model_config = {"populate_by_name": True}


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
    api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("api_key", "apiKey"),
    )
    api_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("api_base_url", "apiBaseUrl"),
    )
    model: str | None = None

    model_config = {"populate_by_name": True}


class KeyCheckResponse(BaseModel):
    success: bool = True
    data: dict[str, Any]


class FavoriteCreateRequest(BaseModel):
    game_id: str = Field(min_length=1, max_length=100)
