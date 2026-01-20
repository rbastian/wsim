"""Persistent game store with JSON file backing.

Extends the in-memory GameStore to automatically persist games to JSON files.
"""

from contextlib import suppress
from pathlib import Path

from wsim_core.models.game import Game
from wsim_core.serialization.game_persistence import GamePersistence

from .store import GameStore


class PersistentGameStore(GameStore):
    """Game store with automatic JSON file persistence.

    All create/update/delete operations are automatically persisted to disk.
    On initialization, loads existing games from the save directory.
    """

    def __init__(self, save_directory: str | Path = "saved_games", auto_load: bool = True) -> None:
        """Initialize persistent game store.

        Args:
            save_directory: Directory to store saved game files
            auto_load: If True, automatically load existing saved games on init
        """
        super().__init__()
        self._persistence = GamePersistence(save_directory)

        if auto_load:
            self._load_existing_games()

    def _load_existing_games(self) -> None:
        """Load all existing saved games into memory."""
        try:
            games = self._persistence.load_all_games()
            for game in games:
                # Use parent class method to avoid re-saving
                super().create_game(game)
        except Exception:
            # If loading fails, start with empty store
            # This prevents startup failures from corrupted files
            pass

    def create_game(self, game: Game) -> None:
        """Store a new game and persist to disk.

        Args:
            game: The game to store

        Raises:
            ValueError: If game ID already exists
            IOError: If persistence fails
        """
        super().create_game(game)
        self._persistence.save_game(game)

    def update_game(self, game: Game) -> None:
        """Update an existing game and persist to disk.

        Args:
            game: The game with updated state

        Raises:
            ValueError: If game doesn't exist
            IOError: If persistence fails
        """
        super().update_game(game)
        self._persistence.save_game(game)

    def delete_game(self, game_id: str) -> None:
        """Delete a game from memory and disk.

        Args:
            game_id: The game identifier

        Raises:
            ValueError: If game doesn't exist
        """
        super().delete_game(game_id)
        # File might not exist if game was created but not saved yet
        with suppress(FileNotFoundError):
            self._persistence.delete_saved_game(game_id)

    def save_all(self) -> int:
        """Explicitly save all in-memory games to disk.

        Useful for ensuring consistency after bulk operations.

        Returns:
            Number of games saved
        """
        games = self.list_games()
        self._persistence.save_all_games(games)
        return len(games)

    def clear_saved_files(self) -> int:
        """Clear all saved game files from disk.

        Does NOT clear in-memory games.

        Returns:
            Number of files deleted
        """
        return self._persistence.clear_all_saved_games()


# Global persistent game store instance
_persistent_game_store: PersistentGameStore | None = None


def get_persistent_game_store(
    save_directory: str | Path = "saved_games", auto_load: bool = True
) -> PersistentGameStore:
    """Get the global persistent game store instance.

    Args:
        save_directory: Directory to store saved game files
        auto_load: If True, automatically load existing saved games on first call

    Returns:
        The persistent game store singleton
    """
    global _persistent_game_store
    if _persistent_game_store is None:
        _persistent_game_store = PersistentGameStore(save_directory, auto_load)
    return _persistent_game_store


def reset_persistent_game_store() -> None:
    """Reset the persistent game store singleton.

    Useful for testing to ensure clean state.
    """
    global _persistent_game_store
    _persistent_game_store = None
