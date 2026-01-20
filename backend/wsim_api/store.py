"""In-memory game store for managing active games."""

import os
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

    If WSIM_ENABLE_PERSISTENCE env var is set to "true", returns a PersistentGameStore.
    Otherwise, returns standard in-memory GameStore.

    Returns:
        The game store singleton (persistent or in-memory based on config)
    """
    global _game_store
    if _game_store is None:
        enable_persistence = os.environ.get("WSIM_ENABLE_PERSISTENCE", "false").lower() == "true"
        if enable_persistence:
            # Import here to avoid circular dependency
            from .persistent_store import PersistentGameStore

            save_dir = os.environ.get("WSIM_SAVE_DIRECTORY", "saved_games")
            _game_store = PersistentGameStore(save_directory=save_dir, auto_load=True)
        else:
            _game_store = GameStore()
    return _game_store
