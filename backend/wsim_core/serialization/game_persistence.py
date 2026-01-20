"""JSON persistence for game state.

Provides functionality to save and load game state to/from JSON files.
Useful for:
- Game state persistence across server restarts
- Manual game state inspection and debugging
- Game replay and analysis
"""

import json
from pathlib import Path

from wsim_core.models.game import Game


class GamePersistence:
    """Handles saving and loading game state to/from JSON files.

    Games are saved as individual JSON files in a configured directory.
    Each game file is named {game_id}.json.
    """

    def __init__(self, save_directory: str | Path = "saved_games") -> None:
        """Initialize persistence manager.

        Args:
            save_directory: Directory to store saved game files (created if missing)
        """
        self.save_directory = Path(save_directory)
        self.save_directory.mkdir(parents=True, exist_ok=True)

    def save_game(self, game: Game) -> Path:
        """Save a game to a JSON file.

        Args:
            game: The game to save

        Returns:
            Path to the saved file

        Raises:
            IOError: If file write fails
        """
        file_path = self.save_directory / f"{game.id}.json"

        # Use Pydantic's model_dump with explicit JSON-serializable mode
        game_data = game.model_dump(mode="json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(game_data, f, indent=2, ensure_ascii=False)

        return file_path

    def load_game(self, game_id: str) -> Game:
        """Load a game from a JSON file.

        Args:
            game_id: The game identifier

        Returns:
            The loaded game

        Raises:
            FileNotFoundError: If game file doesn't exist
            ValueError: If JSON is invalid or doesn't match Game schema
        """
        file_path = self.save_directory / f"{game_id}.json"

        if not file_path.exists():
            raise FileNotFoundError(f"Game file not found: {file_path}")

        with open(file_path, encoding="utf-8") as f:
            game_data = json.load(f)

        # Pydantic will validate and parse the JSON data
        return Game.model_validate(game_data)

    def delete_saved_game(self, game_id: str) -> None:
        """Delete a saved game file.

        Args:
            game_id: The game identifier

        Raises:
            FileNotFoundError: If game file doesn't exist
        """
        file_path = self.save_directory / f"{game_id}.json"

        if not file_path.exists():
            raise FileNotFoundError(f"Game file not found: {file_path}")

        file_path.unlink()

    def list_saved_games(self) -> list[str]:
        """List all saved game IDs.

        Returns:
            List of game IDs that have saved files
        """
        game_files = self.save_directory.glob("*.json")
        return [f.stem for f in game_files if f.is_file()]

    def game_exists(self, game_id: str) -> bool:
        """Check if a saved game file exists.

        Args:
            game_id: The game identifier

        Returns:
            True if saved game exists, False otherwise
        """
        file_path = self.save_directory / f"{game_id}.json"
        return file_path.exists()

    def save_all_games(self, games: list[Game]) -> list[Path]:
        """Save multiple games at once.

        Args:
            games: List of games to save

        Returns:
            List of paths to saved files

        Raises:
            IOError: If any file write fails
        """
        saved_paths = []
        for game in games:
            path = self.save_game(game)
            saved_paths.append(path)
        return saved_paths

    def load_all_games(self) -> list[Game]:
        """Load all saved games from the save directory.

        Returns:
            List of all loaded games

        Raises:
            ValueError: If any game file is invalid
        """
        game_ids = self.list_saved_games()
        games = []
        for game_id in game_ids:
            game = self.load_game(game_id)
            games.append(game)
        return games

    def clear_all_saved_games(self) -> int:
        """Delete all saved game files.

        Returns:
            Number of files deleted
        """
        game_files = list(self.save_directory.glob("*.json"))
        count = 0
        for file_path in game_files:
            if file_path.is_file():
                file_path.unlink()
                count += 1
        return count
