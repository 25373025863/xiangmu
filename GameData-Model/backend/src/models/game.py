"""Game domain model."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Game:
    id: str
    name: str
    platforms: tuple[str, ...]
    genre: str
    price: float
    rating: float
    review_distribution: dict[str, int]
    tags: tuple[str, ...]
    release_date: str
    developer: str
    description: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Game":
        return cls(
            id=data["id"],
            name=data["name"],
            platforms=tuple(data["platforms"]),
            genre=data["genre"],
            price=float(data["price"]),
            rating=float(data["rating"]),
            review_distribution=dict(data.get("review_distribution", {"good": 0, "medium": 0, "poor": 0})),
            tags=tuple(data["tags"]),
            release_date=data["release_date"],
            developer=data["developer"],
            description=data["description"],
        )

    @property
    def price_text(self) -> str:
        return "\u514d\u8d39" if self.price == 0 else f"\u00a5{self.price:.0f}"
