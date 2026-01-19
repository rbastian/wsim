"""In-memory game store for managing active games."""

import uuid

from wsim_core.models.game import Game


class GameStore:
    """In-memory store for active games.

    Provides CRUD operations for game state management.
    Thread-safe for concurrent access (single-process only).
    """

    def __init__(self) -> None:
        """Initialize empty game store."""
        self._games: dict[str, Game] = {}

    def create_game(self, game: Game) -> None:
        """Store a new game.

        Args:
            game: The game to store

        Raises:
            ValueError: If game ID already exists
        """
        if game.id in self._games:
            raise ValueError(f"Game with id {game.id} already exists")
        self._games[game.id] = game

    def get_game(self, game_id: str) -> Game | None:
        """Retrieve a game by ID.

        Args:
            game_id: The game identifier

        Returns:
            The game if found, None otherwise
        """
        return self._games.get(game_id)

    def update_game(self, game: Game) -> None:
        """Update an existing game.

        Args:
            game: The game with updated state

        Raises:
            ValueError: If game doesn't exist
        """
        if game.id not in self._games:
            raise ValueError(f"Game with id {game.id} not found")
        self._games[game.id] = game

    def delete_game(self, game_id: str) -> None:
        """Delete a game.

        Args:
            game_id: The game identifier

        Raises:
            ValueError: If game doesn't exist
        """
        if game_id not in self._games:
            raise ValueError(f"Game with id {game_id} not found")
        del self._games[game_id]

    def list_games(self) -> list[Game]:
        """List all games.

        Returns:
            List of all games in the store
        """
        return list(self._games.values())

    def generate_game_id(self) -> str:
        """Generate a unique game ID.

        Returns:
            A unique game identifier
        """
        return str(uuid.uuid4())


# Global game store instance
_game_store: GameStore | None = None


def get_game_store() -> GameStore:
    """Get the global game store instance.

    Returns:
        The game store singleton
    """
    global _game_store
    if _game_store is None:
        _game_store = GameStore()
    return _game_store
