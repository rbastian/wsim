"""Tests for game persistence functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from wsim_core.models.common import Facing, GamePhase, LoadState, WindDirection
from wsim_core.models.game import Game
from wsim_core.models.hex import HexCoord
from wsim_core.models.ship import Ship
from wsim_core.serialization.game_persistence import GamePersistence


@pytest.fixture
def temp_save_dir():
    """Create temporary directory for test saves."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_game():
    """Create a sample game for testing."""
    ship1 = Ship(
        id="ship1",
        name="Test Ship 1",
        side="P1",
        bow_hex=HexCoord(col=5, row=5),
        stern_hex=HexCoord(col=5, row=6),
        facing=Facing.N,
        battle_sail_speed=4,
        guns_L=10,
        guns_R=10,
        carronades_L=0,
        carronades_R=0,
        hull=12,
        rigging=10,
        crew=10,
        marines=2,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
    )

    ship2 = Ship(
        id="ship2",
        name="Test Ship 2",
        side="P2",
        bow_hex=HexCoord(col=15, row=5),
        stern_hex=HexCoord(col=15, row=6),
        facing=Facing.S,
        battle_sail_speed=4,
        guns_L=10,
        guns_R=10,
        carronades_L=0,
        carronades_R=0,
        hull=12,
        rigging=10,
        crew=10,
        marines=2,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
    )

    game = Game(
        id="test-game-123",
        scenario_id="test_scenario",
        turn_number=1,
        phase=GamePhase.PLANNING,
        map_width=25,
        map_height=20,
        wind_direction=WindDirection.W,
        ships={"ship1": ship1, "ship2": ship2},
        turn_limit=20,
        victory_condition="first_struck",
    )

    return game


def test_persistence_init(temp_save_dir):
    """Test GamePersistence initialization."""
    persistence = GamePersistence(temp_save_dir)
    assert persistence.save_directory == temp_save_dir
    assert temp_save_dir.exists()


def test_persistence_creates_directory():
    """Test that GamePersistence creates save directory if missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "new_directory" / "saves"
        _ = GamePersistence(save_path)
        assert save_path.exists()


def test_save_game(temp_save_dir, sample_game):
    """Test saving a game to JSON."""
    persistence = GamePersistence(temp_save_dir)

    file_path = persistence.save_game(sample_game)

    assert file_path.exists()
    assert file_path.name == f"{sample_game.id}.json"
    assert file_path.parent == temp_save_dir


def test_save_game_creates_valid_json(temp_save_dir, sample_game):
    """Test that saved game is valid JSON."""
    persistence = GamePersistence(temp_save_dir)

    file_path = persistence.save_game(sample_game)

    with open(file_path) as f:
        data = json.load(f)

    assert data["id"] == sample_game.id
    assert data["scenario_id"] == sample_game.scenario_id
    assert data["turn_number"] == sample_game.turn_number
    assert "ship1" in data["ships"]
    assert "ship2" in data["ships"]


def test_load_game(temp_save_dir, sample_game):
    """Test loading a game from JSON."""
    persistence = GamePersistence(temp_save_dir)

    # Save first
    persistence.save_game(sample_game)

    # Load
    loaded_game = persistence.load_game(sample_game.id)

    assert loaded_game.id == sample_game.id
    assert loaded_game.scenario_id == sample_game.scenario_id
    assert loaded_game.turn_number == sample_game.turn_number
    assert loaded_game.phase == sample_game.phase
    assert len(loaded_game.ships) == len(sample_game.ships)


def test_load_game_preserves_ship_data(temp_save_dir, sample_game):
    """Test that loading preserves all ship data."""
    persistence = GamePersistence(temp_save_dir)

    persistence.save_game(sample_game)
    loaded_game = persistence.load_game(sample_game.id)

    ship1_original = sample_game.ships["ship1"]
    ship1_loaded = loaded_game.ships["ship1"]

    assert ship1_loaded.id == ship1_original.id
    assert ship1_loaded.name == ship1_original.name
    assert ship1_loaded.side == ship1_original.side
    assert ship1_loaded.bow_hex == ship1_original.bow_hex
    assert ship1_loaded.stern_hex == ship1_original.stern_hex
    assert ship1_loaded.facing == ship1_original.facing
    assert ship1_loaded.hull == ship1_original.hull
    assert ship1_loaded.rigging == ship1_original.rigging
    assert ship1_loaded.crew == ship1_original.crew
    assert ship1_loaded.marines == ship1_original.marines


def test_load_nonexistent_game(temp_save_dir):
    """Test loading a game that doesn't exist."""
    persistence = GamePersistence(temp_save_dir)

    with pytest.raises(FileNotFoundError):
        persistence.load_game("nonexistent-game")


def test_delete_saved_game(temp_save_dir, sample_game):
    """Test deleting a saved game."""
    persistence = GamePersistence(temp_save_dir)

    file_path = persistence.save_game(sample_game)
    assert file_path.exists()

    persistence.delete_saved_game(sample_game.id)
    assert not file_path.exists()


def test_delete_nonexistent_game(temp_save_dir):
    """Test deleting a game that doesn't exist."""
    persistence = GamePersistence(temp_save_dir)

    with pytest.raises(FileNotFoundError):
        persistence.delete_saved_game("nonexistent-game")


def test_list_saved_games_empty(temp_save_dir):
    """Test listing saved games when directory is empty."""
    persistence = GamePersistence(temp_save_dir)

    game_ids = persistence.list_saved_games()
    assert game_ids == []


def test_list_saved_games(temp_save_dir, sample_game):
    """Test listing saved games."""
    persistence = GamePersistence(temp_save_dir)

    # Save multiple games
    persistence.save_game(sample_game)

    game2 = sample_game.model_copy(deep=True)
    game2.id = "test-game-456"
    persistence.save_game(game2)

    game_ids = persistence.list_saved_games()
    assert len(game_ids) == 2
    assert sample_game.id in game_ids
    assert game2.id in game_ids


def test_game_exists(temp_save_dir, sample_game):
    """Test checking if game file exists."""
    persistence = GamePersistence(temp_save_dir)

    assert not persistence.game_exists(sample_game.id)

    persistence.save_game(sample_game)
    assert persistence.game_exists(sample_game.id)

    persistence.delete_saved_game(sample_game.id)
    assert not persistence.game_exists(sample_game.id)


def test_save_all_games(temp_save_dir, sample_game):
    """Test saving multiple games at once."""
    persistence = GamePersistence(temp_save_dir)

    game2 = sample_game.model_copy(deep=True)
    game2.id = "test-game-456"

    game3 = sample_game.model_copy(deep=True)
    game3.id = "test-game-789"

    saved_paths = persistence.save_all_games([sample_game, game2, game3])

    assert len(saved_paths) == 3
    assert all(p.exists() for p in saved_paths)


def test_load_all_games(temp_save_dir, sample_game):
    """Test loading all saved games."""
    persistence = GamePersistence(temp_save_dir)

    # Save multiple games
    game2 = sample_game.model_copy(deep=True)
    game2.id = "test-game-456"

    persistence.save_game(sample_game)
    persistence.save_game(game2)

    # Load all
    loaded_games = persistence.load_all_games()

    assert len(loaded_games) == 2
    game_ids = {g.id for g in loaded_games}
    assert sample_game.id in game_ids
    assert game2.id in game_ids


def test_clear_all_saved_games(temp_save_dir, sample_game):
    """Test clearing all saved games."""
    persistence = GamePersistence(temp_save_dir)

    # Save multiple games
    game2 = sample_game.model_copy(deep=True)
    game2.id = "test-game-456"

    persistence.save_game(sample_game)
    persistence.save_game(game2)

    assert len(persistence.list_saved_games()) == 2

    count = persistence.clear_all_saved_games()
    assert count == 2
    assert len(persistence.list_saved_games()) == 0


def test_save_game_with_event_log(temp_save_dir, sample_game):
    """Test saving game with event log entries."""
    from wsim_core.models.events import EventLogEntry

    persistence = GamePersistence(temp_save_dir)

    # Add event to game
    event = EventLogEntry(
        turn_number=1,
        phase=GamePhase.MOVEMENT,
        event_type="movement",
        summary="Ship moved",
    )
    sample_game.add_event(event)

    persistence.save_game(sample_game)
    loaded_game = persistence.load_game(sample_game.id)

    assert len(loaded_game.event_log) == 1
    assert loaded_game.event_log[0].summary == "Ship moved"


def test_save_game_preserves_optional_fields(temp_save_dir, sample_game):
    """Test that optional fields are preserved."""
    persistence = GamePersistence(temp_save_dir)

    # Set optional fields
    sample_game.game_ended = True
    sample_game.winner = "P1"

    persistence.save_game(sample_game)
    loaded_game = persistence.load_game(sample_game.id)

    assert loaded_game.game_ended is True
    assert loaded_game.winner == "P1"


def test_roundtrip_multiple_times(temp_save_dir, sample_game):
    """Test saving and loading multiple times."""
    persistence = GamePersistence(temp_save_dir)

    # Save and load multiple times
    for i in range(3):
        sample_game.turn_number = i + 1
        persistence.save_game(sample_game)
        loaded_game = persistence.load_game(sample_game.id)
        assert loaded_game.turn_number == i + 1
