"""Tests for FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from wsim_api.main import app
from wsim_api.store import get_game_store

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_game_store() -> None:
    """Reset game store before each test."""
    store = get_game_store()
    # Clear all games
    for game in list(store.list_games()):
        store.delete_game(game.id)


def test_root() -> None:
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Wooden Ships & Iron Men API"
    assert data["version"] == "0.1.0"


def test_health() -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_scenarios() -> None:
    """Test listing available scenarios."""
    response = client.get("/games/scenarios")
    assert response.status_code == 200

    scenarios = response.json()
    assert isinstance(scenarios, list)
    assert len(scenarios) > 0

    # Check that we have expected scenarios
    scenario_ids = [s["id"] for s in scenarios]
    assert "mvp_frigate_duel_v1" in scenario_ids
    assert "mvp_crossing_paths_v1" in scenario_ids
    assert "mvp_two_ship_line_battle_v1" in scenario_ids

    # Check scenario structure
    for scenario in scenarios:
        assert "id" in scenario
        assert "name" in scenario
        assert "description" in scenario


def test_create_game() -> None:
    """Test creating a new game from a scenario."""
    response = client.post(
        "/games",
        json={"scenario_id": "mvp_frigate_duel_v1"},
    )
    assert response.status_code == 201

    data = response.json()
    assert "game_id" in data
    assert "state" in data

    game_state = data["state"]
    assert game_state["id"] == data["game_id"]
    assert game_state["scenario_id"] == "mvp_frigate_duel_v1"
    assert game_state["turn_number"] == 1
    assert game_state["phase"] == "planning"
    assert len(game_state["ships"]) == 2


def test_create_game_invalid_scenario() -> None:
    """Test creating game with non-existent scenario."""
    response = client.post(
        "/games",
        json={"scenario_id": "nonexistent_scenario"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_game() -> None:
    """Test retrieving a game by ID."""
    # First create a game
    create_response = client.post(
        "/games",
        json={"scenario_id": "mvp_frigate_duel_v1"},
    )
    assert create_response.status_code == 201
    game_id = create_response.json()["game_id"]

    # Now retrieve it
    get_response = client.get(f"/games/{game_id}")
    assert get_response.status_code == 200

    game_state = get_response.json()
    assert game_state["id"] == game_id
    assert game_state["scenario_id"] == "mvp_frigate_duel_v1"


def test_get_game_not_found() -> None:
    """Test retrieving non-existent game."""
    response = client.get("/games/nonexistent-game-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_game() -> None:
    """Test deleting a game."""
    # First create a game
    create_response = client.post(
        "/games",
        json={"scenario_id": "mvp_frigate_duel_v1"},
    )
    assert create_response.status_code == 201
    game_id = create_response.json()["game_id"]

    # Delete it
    delete_response = client.delete(f"/games/{game_id}")
    assert delete_response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/games/{game_id}")
    assert get_response.status_code == 404


def test_delete_game_not_found() -> None:
    """Test deleting non-existent game."""
    response = client.delete("/games/nonexistent-game-id")
    assert response.status_code == 404
