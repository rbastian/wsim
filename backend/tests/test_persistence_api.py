"""Tests for persistence API endpoints."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wsim_api.main import app
from wsim_api.persistent_store import PersistentGameStore
from wsim_core.models.common import Facing, GamePhase, LoadState, WindDirection
from wsim_core.models.game import Game
from wsim_core.models.hex import HexCoord
from wsim_core.models.ship import Ship

client = TestClient(app)


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
        id="test-game-api",
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
def persistent_store(temp_save_dir):
    """Set up persistent store for testing and clean up afterwards."""
    import wsim_api.store

    # Save original store
    original_store = wsim_api.store._game_store

    # Create persistent store
    store = PersistentGameStore(save_directory=temp_save_dir, auto_load=False)
    wsim_api.store._game_store = store

    yield store

    # Restore original store
    wsim_api.store._game_store = original_store


@pytest.fixture
def non_persistent_store():
    """Set up non-persistent store for testing 503 errors."""
    import wsim_api.store
    from wsim_api.store import GameStore

    # Save original store
    original_store = wsim_api.store._game_store

    # Create non-persistent store
    store = GameStore()
    wsim_api.store._game_store = store

    yield store

    # Restore original store
    wsim_api.store._game_store = original_store


def test_save_game_success(persistent_store, sample_game):
    """Test save_game endpoint with valid game."""
    # Create game in store
    persistent_store.create_game(sample_game)

    # Save via API
    response = client.post(f"/persistence/games/{sample_game.id}/save")

    assert response.status_code == 200
    data = response.json()
    assert data["game_id"] == sample_game.id
    assert "file_path" in data
    assert sample_game.id in data["file_path"]

    # Verify file exists
    assert persistent_store._persistence.game_exists(sample_game.id)


def test_save_game_not_found(persistent_store):
    """Test save_game with non-existent game (404 error)."""
    response = client.post("/persistence/games/nonexistent-game/save")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_save_game_persistence_not_enabled(non_persistent_store, sample_game):
    """Test save_game when persistence not enabled (503 error)."""
    # Create game in non-persistent store
    non_persistent_store.create_game(sample_game)

    response = client.post(f"/persistence/games/{sample_game.id}/save")

    assert response.status_code == 503
    assert "persistence not enabled" in response.json()["detail"].lower()


def test_load_game_success(persistent_store, sample_game):
    """Test load_game endpoint with valid saved game."""
    # Save game to disk
    persistent_store._persistence.save_game(sample_game)

    # Load via API
    response = client.post(f"/persistence/games/{sample_game.id}/load")

    assert response.status_code == 200
    data = response.json()
    assert data["game_id"] == sample_game.id
    assert data["success"] is True

    # Verify game is now in memory
    loaded_game = persistent_store.get_game(sample_game.id)
    assert loaded_game is not None
    assert loaded_game.id == sample_game.id


def test_load_game_not_found(persistent_store):
    """Test load_game with non-existent file (404 error)."""
    response = client.post("/persistence/games/nonexistent-game/load")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_load_game_invalid_file(persistent_store, temp_save_dir):
    """Test load_game with invalid game file (400 error)."""
    # Create an invalid JSON file
    invalid_file = temp_save_dir / "invalid-game.json"
    invalid_file.write_text("not valid json {{{")

    response = client.post("/persistence/games/invalid-game/load")

    assert response.status_code == 400
    assert "invalid game file" in response.json()["detail"].lower()


def test_load_game_persistence_not_enabled(non_persistent_store):
    """Test load_game when persistence not enabled (503 error)."""
    response = client.post("/persistence/games/some-game/load")

    assert response.status_code == 503
    assert "persistence not enabled" in response.json()["detail"].lower()


def test_save_all_games_success(persistent_store, sample_game):
    """Test save_all_games endpoint."""
    # Create multiple games
    persistent_store.create_game(sample_game)

    game2 = sample_game.model_copy(deep=True)
    game2.id = "test-game-2"
    persistent_store.create_game(game2)

    # Save all via API
    response = client.post("/persistence/save-all")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["game_ids"]) == 2
    assert sample_game.id in data["game_ids"]
    assert game2.id in data["game_ids"]

    # Verify files exist
    assert persistent_store._persistence.game_exists(sample_game.id)
    assert persistent_store._persistence.game_exists(game2.id)


def test_save_all_games_empty(persistent_store):
    """Test save_all_games when no games exist."""
    response = client.post("/persistence/save-all")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["game_ids"] == []


def test_save_all_games_persistence_not_enabled(non_persistent_store):
    """Test save_all_games when persistence not enabled (503 error)."""
    response = client.post("/persistence/save-all")

    assert response.status_code == 503
    assert "persistence not enabled" in response.json()["detail"].lower()


def test_list_saved_games_success(persistent_store, sample_game):
    """Test list_saved_games endpoint."""
    # Save multiple games
    persistent_store._persistence.save_game(sample_game)

    game2 = sample_game.model_copy(deep=True)
    game2.id = "test-game-2"
    persistent_store._persistence.save_game(game2)

    # List via API
    response = client.get("/persistence/saved-games")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["game_ids"]) == 2
    assert sample_game.id in data["game_ids"]
    assert game2.id in data["game_ids"]


def test_list_saved_games_empty(persistent_store):
    """Test list_saved_games when no saved games exist."""
    response = client.get("/persistence/saved-games")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["game_ids"] == []


def test_list_saved_games_persistence_not_enabled(non_persistent_store):
    """Test list_saved_games when persistence not enabled (503 error)."""
    response = client.get("/persistence/saved-games")

    assert response.status_code == 503
    assert "persistence not enabled" in response.json()["detail"].lower()


def test_clear_saved_games_success(persistent_store, sample_game):
    """Test clear_saved_games endpoint."""
    # Save multiple games
    persistent_store._persistence.save_game(sample_game)

    game2 = sample_game.model_copy(deep=True)
    game2.id = "test-game-2"
    persistent_store._persistence.save_game(game2)

    # Clear via API
    response = client.delete("/persistence/saved-games")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2

    # Verify files are gone
    assert not persistent_store._persistence.game_exists(sample_game.id)
    assert not persistent_store._persistence.game_exists(game2.id)


def test_clear_saved_games_empty(persistent_store):
    """Test clear_saved_games when no saved games exist."""
    response = client.delete("/persistence/saved-games")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0


def test_clear_saved_games_persistence_not_enabled(non_persistent_store):
    """Test clear_saved_games when persistence not enabled (503 error)."""
    response = client.delete("/persistence/saved-games")

    assert response.status_code == 503
    assert "persistence not enabled" in response.json()["detail"].lower()


def test_delete_saved_game_success(persistent_store, sample_game):
    """Test delete_saved_game with valid file."""
    # Save game
    persistent_store._persistence.save_game(sample_game)

    # Delete via API
    response = client.delete(f"/persistence/games/{sample_game.id}/saved")

    assert response.status_code == 200
    data = response.json()
    assert "deleted" in data["message"].lower()
    assert data["game_id"] == sample_game.id

    # Verify file is gone
    assert not persistent_store._persistence.game_exists(sample_game.id)


def test_delete_saved_game_not_found(persistent_store):
    """Test delete_saved_game with non-existent file (404 error)."""
    response = client.delete("/persistence/games/nonexistent-game/saved")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_saved_game_persistence_not_enabled(non_persistent_store):
    """Test delete_saved_game when persistence not enabled (503 error)."""
    response = client.delete("/persistence/games/some-game/saved")

    assert response.status_code == 503
    assert "persistence not enabled" in response.json()["detail"].lower()


def test_save_and_load_roundtrip(persistent_store, sample_game):
    """Test full save and load roundtrip maintains game state."""
    # Save game directly to disk (not through store which would auto-persist)
    file_path = persistent_store._persistence.save_game(sample_game)
    assert file_path.exists()

    # Load via API
    response = client.post(f"/persistence/games/{sample_game.id}/load")
    assert response.status_code == 200

    # Verify state
    loaded_game = persistent_store.get_game(sample_game.id)
    assert loaded_game is not None
    assert loaded_game.turn_number == sample_game.turn_number
    assert loaded_game.phase == sample_game.phase
    assert len(loaded_game.ships) == len(sample_game.ships)
