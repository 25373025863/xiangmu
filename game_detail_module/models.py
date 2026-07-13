from pydantic import BaseModel, Field


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
