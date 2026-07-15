from backend.src.repositories.game_repository import GameRepository


class GameService:
    def __init__(self, repository: GameRepository | None = None) -> None:
        self._repository = repository or GameRepository()

    def list_games(
        self,
        keyword: str = "",
        genre: str = "",
        platform: str = "",
        tag: str = "",
    ) -> list[dict]:
        games = self._repository.get_all()
        keyword = keyword.strip().casefold()
        if keyword:
            games = [game for game in games if keyword in self._searchable_text(game)]
        if genre:
            games = [game for game in games if genre in game.get("genres", [])]
        if platform:
            games = [game for game in games if platform in game.get("platforms", [])]
        if tag:
            games = [game for game in games if tag in game.get("tags", [])]
        return sorted(games, key=lambda game: float(game.get("score") or 0), reverse=True)

    def get_game(self, game_id: str) -> dict | None:
        return self._repository.get_by_id(game_id)

    @staticmethod
    def _searchable_text(game: dict) -> str:
        values = [
            game.get("title", ""),
            game.get("description", ""),
            *game.get("genres", []),
            *game.get("platforms", []),
            *game.get("tags", []),
        ]
        return " ".join(str(value) for value in values).casefold()
