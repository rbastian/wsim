"""Tests for persistent game store."""

import tempfile
from pathlib import Path

import pytest

from wsim_api.persistent_store import PersistentGameStore, reset_persistent_game_store
from wsim_core.models.common import Facing, GamePhase, LoadState, WindDirection
from wsim_core.models.game import Game
from wsim_core.models.hex import HexCoord
from wsim_core.models.ship import Ship


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

    game = Game(
        id="test-game-persist",
        scenario_id="test_scenario",
        turn_number=1,
        phase=GamePhase.PLANNING,
        map_width=25,
        map_height=20,
        wind_direction=WindDirection.W,
        ships={"ship1": ship1},
        turn_limit=20,
        victory_condition="first_struck",
    )

    return game


@pytest.fixture
def store(temp_save_dir):
    """Create a persistent store with temporary directory."""
    return PersistentGameStore(save_directory=temp_save_dir, auto_load=False)


def test_persistent_store_init(temp_save_dir):
    """Test PersistentGameStore initialization."""
    store = PersistentGameStore(save_directory=temp_save_dir, auto_load=False)
    assert store._persistence.save_directory == temp_save_dir


def test_create_game_persists(store, sample_game):
    """Test that creating a game persists it to disk."""
    store.create_game(sample_game)

    # Check in memory
    assert store.get_game(sample_game.id) is not None

    # Check on disk
    assert store._persistence.game_exists(sample_game.id)


def test_update_game_persists(store, sample_game):
    """Test that updating a game persists changes to disk."""
    store.create_game(sample_game)

    # Update game
    sample_game.turn_number = 5
    store.update_game(sample_game)

    # Load from disk and verify
    loaded = store._persistence.load_game(sample_game.id)
    assert loaded.turn_number == 5


def test_delete_game_removes_file(store, sample_game):
    """Test that deleting a game removes the file."""
    store.create_game(sample_game)

    assert store._persistence.game_exists(sample_game.id)

    store.delete_game(sample_game.id)

    assert not store._persistence.game_exists(sample_game.id)


def test_auto_load_existing_games(temp_save_dir, sample_game):
    """Test that auto_load loads existing saved games."""
    # Create and save a game
    store1 = PersistentGameStore(save_directory=temp_save_dir, auto_load=False)
    store1.create_game(sample_game)

    # Create new store with auto_load
    store2 = PersistentGameStore(save_directory=temp_save_dir, auto_load=True)

    # Game should be loaded
    loaded_game = store2.get_game(sample_game.id)
    assert loaded_game is not None
    assert loaded_game.id == sample_game.id


def test_auto_load_handles_corrupted_files(temp_save_dir):
    """Test that auto_load handles corrupted files gracefully."""
    # Create a corrupted file
    corrupted_file = temp_save_dir / "corrupted.json"
    corrupted_file.write_text("not valid json {{{")

    # Should not raise error
    store = PersistentGameStore(save_directory=temp_save_dir, auto_load=True)

    # Store should be empty
    assert len(store.list_games()) == 0


def test_save_all(temp_save_dir, sample_game):
    """Test explicit save_all operation."""
    store = PersistentGameStore(save_directory=temp_save_dir, auto_load=False)

    # Create game without auto-persist (using parent method)
    from wsim_api.store import GameStore

    GameStore.create_game(store, sample_game)

    # Manually save all
    count = store.save_all()

    assert count == 1
    assert store._persistence.game_exists(sample_game.id)


def test_clear_saved_files(store, sample_game):
    """Test clearing saved files."""
    store.create_game(sample_game)

    # Clear files but not memory
    count = store.clear_saved_files()

    assert count == 1
    # Still in memory
    assert store.get_game(sample_game.id) is not None
    # Not on disk
    assert not store._persistence.game_exists(sample_game.id)


def test_persistence_survives_restart(temp_save_dir, sample_game):
    """Test that games persist across store recreations."""
    # Create store and game
    store1 = PersistentGameStore(save_directory=temp_save_dir, auto_load=False)
    store1.create_game(sample_game)

    # Update game state
    sample_game.turn_number = 7
    sample_game.phase = GamePhase.COMBAT
    store1.update_game(sample_game)

    # Simulate restart: create new store
    store2 = PersistentGameStore(save_directory=temp_save_dir, auto_load=True)

    # Game should be loaded with updated state
    loaded = store2.get_game(sample_game.id)
    assert loaded is not None
    assert loaded.turn_number == 7
    assert loaded.phase == GamePhase.COMBAT


def test_multiple_games_persist(temp_save_dir, sample_game):
    """Test that multiple games persist correctly."""
    store = PersistentGameStore(save_directory=temp_save_dir, auto_load=False)

    # Create multiple games
    game2 = sample_game.model_copy(deep=True)
    game2.id = "game-2"

    game3 = sample_game.model_copy(deep=True)
    game3.id = "game-3"

    store.create_game(sample_game)
    store.create_game(game2)
    store.create_game(game3)

    # Restart store
    store2 = PersistentGameStore(save_directory=temp_save_dir, auto_load=True)

    # All games should be loaded
    assert len(store2.list_games()) == 3
    assert store2.get_game(sample_game.id) is not None
    assert store2.get_game("game-2") is not None
    assert store2.get_game("game-3") is not None


def test_reset_persistent_game_store():
    """Test resetting the global store singleton."""
    reset_persistent_game_store()
    # After reset, get should create new instance
    # This is more of a smoke test to ensure the function works


def test_delete_game_handles_missing_file(store, sample_game):
    """Test deleting game when file doesn't exist."""
    # Add to memory without persisting
    from wsim_api.store import GameStore

    GameStore.create_game(store, sample_game)

    # Delete should not raise error even if file missing
    store.delete_game(sample_game.id)

    # Game should be gone from memory
    assert store.get_game(sample_game.id) is None


def test_get_persistent_game_store_singleton(temp_save_dir):
    """Test get_persistent_game_store creates singleton."""
    from wsim_api.persistent_store import get_persistent_game_store

    # Reset singleton first
    reset_persistent_game_store()

    # First call creates instance
    store1 = get_persistent_game_store(save_directory=temp_save_dir, auto_load=False)
    assert store1 is not None

    # Second call returns same instance
    store2 = get_persistent_game_store(save_directory=temp_save_dir, auto_load=False)
    assert store1 is store2

    # Cleanup
    reset_persistent_game_store()
