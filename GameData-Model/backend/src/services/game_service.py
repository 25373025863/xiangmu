"""Search, filter, sort, and summary logic for the game catalogue."""

from collections import Counter

from backend.src.models.game import Game
from backend.src.repositories.game_repository import GameRepository


class GameService:
    def __init__(self, repository: GameRepository | None = None) -> None:
        self._repository = repository or GameRepository()

    def list_games(
        self,
        keyword: str = "",
        genre: str = "\u5168\u90e8\u7c7b\u578b",
        platform: str = "\u5168\u90e8\u5e73\u53f0",
        price_range: str = "\u5168\u90e8\u4ef7\u683c",
        sort_by: str = "\u8bc4\u5206\u4ece\u9ad8\u5230\u4f4e",
        tag: str = "\u5168\u90e8\u6807\u7b7e",
    ) -> list[Game]:
        games = self._repository.get_all()
        keyword = keyword.strip().casefold()
        if keyword:
            games = [game for game in games if keyword in self._searchable_text(game)]
        if genre != "\u5168\u90e8\u7c7b\u578b":
            games = [game for game in games if game.genre == genre]
        if platform != "\u5168\u90e8\u5e73\u53f0":
            games = [game for game in games if platform in game.platforms]
        if tag != "\u5168\u90e8\u6807\u7b7e":
            games = [game for game in games if tag in game.tags]
        games = self._filter_by_price(games, price_range)

        if sort_by == "\u4ef7\u683c\u4ece\u4f4e\u5230\u9ad8":
            return sorted(games, key=lambda game: (game.price, -game.rating))
        if sort_by == "\u540d\u79f0\u6392\u5e8f":
            return sorted(games, key=lambda game: game.name.casefold())
        return sorted(games, key=lambda game: (-game.rating, game.price))

    def get_game(self, game_id: str) -> Game | None:
        return self._repository.get_by_id(game_id)

    def get_filter_options(self) -> tuple[list[str], list[str]]:
        games = self._repository.get_all()
        genres = sorted({game.genre for game in games})
        platforms = sorted({platform for game in games for platform in game.platforms})
        return genres, platforms

    def get_statistics(self) -> dict[str, str]:
        games = self._repository.get_all()
        all_tags = Counter(tag for game in games for tag in game.tags)
        average_rating = sum(game.rating for game in games) / len(games) if games else 0
        return {
            "total": str(len(games)),
            "genres": str(len({game.genre for game in games})),
            "average_rating": f"{average_rating:.1f}",
            "top_tag": all_tags.most_common(1)[0][0] if all_tags else "-",
        }

    @staticmethod
    def _searchable_text(game: Game) -> str:
        values = [game.name, game.genre, game.description, *game.platforms, *game.tags]
        return " ".join(values).casefold()

    @staticmethod
    def _filter_by_price(games: list[Game], price_range: str) -> list[Game]:
        if price_range == "\u514d\u8d39":
            return [game for game in games if game.price == 0]
        if price_range == "\u00a51 - \u00a5100":
            return [game for game in games if 0 < game.price <= 100]
        if price_range == "\u00a5101 - \u00a5200":
            return [game for game in games if 100 < game.price <= 200]
        if price_range == "\u00a5201\u53ca\u4ee5\u4e0a":
            return [game for game in games if game.price > 200]
        return games
