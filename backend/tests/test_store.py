"""Tests for in-memory game store."""

import tempfile

import pytest

from wsim_api.store import GameStore
from wsim_core.models.common import Facing, GamePhase, LoadState, WindDirection
from wsim_core.models.game import Game
from wsim_core.models.hex import HexCoord
from wsim_core.models.ship import Ship


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
        id="test-game-store",
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
def store():
    """Create a game store instance."""
    return GameStore()


def test_create_duplicate_game_raises_error(store, sample_game):
    """Test that creating a game with duplicate ID raises ValueError."""
    store.create_game(sample_game)

    # Try to create another game with same ID
    with pytest.raises(ValueError, match=f"Game with id {sample_game.id} already exists"):
        store.create_game(sample_game)


def test_update_nonexistent_game_raises_error(store, sample_game):
    """Test that updating a non-existent game raises ValueError."""
    with pytest.raises(ValueError, match=f"Game with id {sample_game.id} not found"):
        store.update_game(sample_game)


def test_get_game_store_with_persistence(monkeypatch):
    """Test get_game_store with WSIM_ENABLE_PERSISTENCE=true."""
    # Clear singleton
    import wsim_api.store
    from wsim_api.store import get_game_store

    wsim_api.store._game_store = None

    # Set environment variables
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("WSIM_ENABLE_PERSISTENCE", "true")
        monkeypatch.setenv("WSIM_SAVE_DIRECTORY", tmpdir)

        # Get store - should create PersistentGameStore
        store = get_game_store()

        # Check it's a PersistentGameStore
        from wsim_api.persistent_store import PersistentGameStore

        assert isinstance(store, PersistentGameStore)

        # Cleanup
        wsim_api.store._game_store = None


def test_get_game_store_without_persistence(monkeypatch):
    """Test get_game_store with WSIM_ENABLE_PERSISTENCE=false."""
    import wsim_api.store
    from wsim_api.store import get_game_store

    wsim_api.store._game_store = None

    # Set environment variable
    monkeypatch.setenv("WSIM_ENABLE_PERSISTENCE", "false")

    # Get store - should create regular GameStore
    store = get_game_store()
    assert isinstance(store, GameStore)

    # Should not be PersistentGameStore
    from wsim_api.persistent_store import PersistentGameStore

    assert not isinstance(store, PersistentGameStore)

    # Cleanup
    wsim_api.store._game_store = None
