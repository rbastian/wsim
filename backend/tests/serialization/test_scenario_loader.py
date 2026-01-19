"""Tests for scenario loader."""

import json
import tempfile
from pathlib import Path

import pytest

from wsim_core.models.common import Facing, LoadState, Side, WindDirection
from wsim_core.models.hex import HexCoord
from wsim_core.serialization.scenario_loader import (
    ScenarioLoadError,
    initialize_game_from_scenario,
    load_scenario_from_dict,
    load_scenario_from_file,
)


def test_load_valid_scenario_from_dict():
    """Test loading a valid scenario from a dictionary."""
    data = {
        "id": "test_scenario",
        "name": "Test Scenario",
        "description": "A test scenario",
        "map": {"width": 10, "height": 10},
        "wind": {"direction": "N"},
        "turn_limit": 10,
        "victory": {"type": "first_struck"},
        "ships": [
            {
                "id": "ship1",
                "side": "P1",
                "name": "Test Ship",
                "battle_sail_speed": 3,
                "start": {"bow": [5, 5], "facing": "N"},
                "guns": {"L": 10, "R": 10},
                "carronades": {"L": 0, "R": 0},
                "hull": 12,
                "rigging": 10,
                "crew": 10,
                "marines": 2,
                "initial_load": {"L": "R", "R": "R"},
            }
        ],
    }

    scenario = load_scenario_from_dict(data)

    assert scenario.id == "test_scenario"
    assert scenario.name == "Test Scenario"
    assert scenario.map.width == 10
    assert scenario.map.height == 10
    assert scenario.wind.direction == WindDirection.N
    assert scenario.turn_limit == 10
    assert len(scenario.ships) == 1
    assert scenario.ships[0].id == "ship1"


def test_load_scenario_with_optional_fields():
    """Test loading a scenario with optional fields."""
    data = {
        "id": "test_scenario",
        "name": "Test Scenario",
        "description": "A test scenario",
        "map": {"width": 10, "height": 10},
        "wind": {"direction": "N"},
        "victory": {"type": "score_after_turns", "metric": "remaining_hull"},
        "ships": [
            {
                "id": "ship1",
                "side": "P1",
                "name": "Test Ship",
                "battle_sail_speed": 3,
                "start": {"bow": [5, 5], "facing": "N"},
                "guns": {"L": 10, "R": 10},
                "hull": 12,
                "rigging": 10,
                "crew": 10,
                "marines": 2,
                "initial_load": {"L": "R", "R": "R"},
            }
        ],
    }

    scenario = load_scenario_from_dict(data)

    assert scenario.turn_limit is None
    assert scenario.ships[0].carronades.L == 0
    assert scenario.ships[0].carronades.R == 0


def test_load_scenario_missing_required_field():
    """Test that loading fails when required field is missing."""
    data = {
        "id": "test_scenario",
        "name": "Test Scenario",
        # Missing description
        "map": {"width": 10, "height": 10},
        "wind": {"direction": "N"},
        "victory": {"type": "first_struck"},
        "ships": [],
    }

    with pytest.raises(ScenarioLoadError, match="validation failed"):
        load_scenario_from_dict(data)


def test_load_scenario_invalid_wind_direction():
    """Test that loading fails with invalid wind direction."""
    data = {
        "id": "test_scenario",
        "name": "Test Scenario",
        "description": "A test scenario",
        "map": {"width": 10, "height": 10},
        "wind": {"direction": "INVALID"},
        "victory": {"type": "first_struck"},
        "ships": [],
    }

    with pytest.raises(ScenarioLoadError, match="validation failed"):
        load_scenario_from_dict(data)


def test_load_scenario_duplicate_ship_ids():
    """Test that loading fails when ship IDs are not unique."""
    data = {
        "id": "test_scenario",
        "name": "Test Scenario",
        "description": "A test scenario",
        "map": {"width": 10, "height": 10},
        "wind": {"direction": "N"},
        "victory": {"type": "first_struck"},
        "ships": [
            {
                "id": "ship1",
                "side": "P1",
                "name": "Test Ship 1",
                "battle_sail_speed": 3,
                "start": {"bow": [5, 5], "facing": "N"},
                "guns": {"L": 10, "R": 10},
                "hull": 12,
                "rigging": 10,
                "crew": 10,
                "marines": 2,
                "initial_load": {"L": "R", "R": "R"},
            },
            {
                "id": "ship1",  # Duplicate ID
                "side": "P2",
                "name": "Test Ship 2",
                "battle_sail_speed": 3,
                "start": {"bow": [6, 6], "facing": "S"},
                "guns": {"L": 10, "R": 10},
                "hull": 12,
                "rigging": 10,
                "crew": 10,
                "marines": 2,
                "initial_load": {"L": "R", "R": "R"},
            },
        ],
    }

    with pytest.raises(ScenarioLoadError, match="Duplicate ship IDs"):
        load_scenario_from_dict(data)


def test_load_scenario_ship_out_of_bounds():
    """Test that loading fails when ship starts outside map bounds."""
    data = {
        "id": "test_scenario",
        "name": "Test Scenario",
        "description": "A test scenario",
        "map": {"width": 10, "height": 10},
        "wind": {"direction": "N"},
        "victory": {"type": "first_struck"},
        "ships": [
            {
                "id": "ship1",
                "side": "P1",
                "name": "Test Ship",
                "battle_sail_speed": 3,
                "start": {"bow": [15, 15], "facing": "N"},  # Out of bounds
                "guns": {"L": 10, "R": 10},
                "hull": 12,
                "rigging": 10,
                "crew": 10,
                "marines": 2,
                "initial_load": {"L": "R", "R": "R"},
            }
        ],
    }

    with pytest.raises(ScenarioLoadError, match="outside map bounds"):
        load_scenario_from_dict(data)


def test_load_scenario_from_file():
    """Test loading a scenario from a JSON file."""
    data = {
        "id": "test_scenario",
        "name": "Test Scenario",
        "description": "A test scenario",
        "map": {"width": 10, "height": 10},
        "wind": {"direction": "N"},
        "victory": {"type": "first_struck"},
        "ships": [
            {
                "id": "ship1",
                "side": "P1",
                "name": "Test Ship",
                "battle_sail_speed": 3,
                "start": {"bow": [5, 5], "facing": "N"},
                "guns": {"L": 10, "R": 10},
                "hull": 12,
                "rigging": 10,
                "crew": 10,
                "marines": 2,
                "initial_load": {"L": "R", "R": "R"},
            }
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        temp_path = f.name

    try:
        scenario = load_scenario_from_file(temp_path)
        assert scenario.id == "test_scenario"
    finally:
        Path(temp_path).unlink()


def test_load_scenario_from_nonexistent_file():
    """Test that loading fails when file doesn't exist."""
    with pytest.raises(ScenarioLoadError, match="not found"):
        load_scenario_from_file("/nonexistent/path.json")


def test_load_scenario_from_invalid_json_file():
    """Test that loading fails when JSON is malformed."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("{ invalid json }")
        temp_path = f.name

    try:
        with pytest.raises(ScenarioLoadError, match="Invalid JSON"):
            load_scenario_from_file(temp_path)
    finally:
        Path(temp_path).unlink()


def test_initialize_game_from_scenario():
    """Test initializing a game from a scenario."""
    data = {
        "id": "test_scenario",
        "name": "Test Scenario",
        "description": "A test scenario",
        "map": {"width": 10, "height": 10},
        "wind": {"direction": "N"},
        "turn_limit": 10,
        "victory": {"type": "first_struck"},
        "ships": [
            {
                "id": "ship1",
                "side": "P1",
                "name": "Test Ship 1",
                "battle_sail_speed": 3,
                "start": {"bow": [5, 5], "facing": "E"},
                "guns": {"L": 10, "R": 10},
                "carronades": {"L": 2, "R": 2},
                "hull": 12,
                "rigging": 10,
                "crew": 10,
                "marines": 2,
                "initial_load": {"L": "R", "R": "E"},
            },
            {
                "id": "ship2",
                "side": "P2",
                "name": "Test Ship 2",
                "battle_sail_speed": 4,
                "start": {"bow": [8, 8], "facing": "W"},
                "guns": {"L": 8, "R": 8},
                "hull": 10,
                "rigging": 8,
                "crew": 8,
                "marines": 1,
                "initial_load": {"L": "R", "R": "R"},
            },
        ],
    }

    scenario = load_scenario_from_dict(data)
    game = initialize_game_from_scenario(scenario, "game123")

    assert game.id == "game123"
    assert game.scenario_id == "test_scenario"
    assert game.turn_number == 1
    assert game.map_width == 10
    assert game.map_height == 10
    assert game.wind_direction == WindDirection.N
    assert game.turn_limit == 10
    assert game.victory_condition == "first_struck"
    assert len(game.ships) == 2

    # Check first ship
    ship1 = game.ships["ship1"]
    assert ship1.id == "ship1"
    assert ship1.name == "Test Ship 1"
    assert ship1.side == Side.P1
    assert ship1.bow_hex == HexCoord(col=5, row=5)
    assert ship1.stern_hex == HexCoord(col=4, row=5)  # W from bow when facing E
    assert ship1.facing == Facing.E
    assert ship1.battle_sail_speed == 3
    assert ship1.guns_L == 10
    assert ship1.guns_R == 10
    assert ship1.carronades_L == 2
    assert ship1.carronades_R == 2
    assert ship1.hull == 12
    assert ship1.rigging == 10
    assert ship1.crew == 10
    assert ship1.marines == 2
    assert ship1.load_L == LoadState.ROUNDSHOT
    assert ship1.load_R == LoadState.EMPTY
    assert ship1.fouled is False
    assert ship1.struck is False
    assert ship1.turns_without_bow_advance == 0

    # Check second ship
    ship2 = game.ships["ship2"]
    assert ship2.id == "ship2"
    assert ship2.side == Side.P2
    assert ship2.bow_hex == HexCoord(col=8, row=8)
    assert ship2.stern_hex == HexCoord(col=9, row=8)  # E from bow when facing W
    assert ship2.facing == Facing.W


def test_stern_calculation_all_directions():
    """Test stern hex calculation for all facing directions."""
    data = {
        "id": "test_scenario",
        "name": "Test Scenario",
        "description": "A test scenario",
        "map": {"width": 20, "height": 20},
        "wind": {"direction": "N"},
        "victory": {"type": "first_struck"},
        "ships": [
            {
                "id": f"ship_{facing.lower()}",
                "side": "P1",
                "name": f"Ship {facing}",
                "battle_sail_speed": 3,
                "start": {"bow": [10, 10], "facing": facing},
                "guns": {"L": 10, "R": 10},
                "hull": 12,
                "rigging": 10,
                "crew": 10,
                "marines": 2,
                "initial_load": {"L": "R", "R": "R"},
            }
            for facing in ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        ],
    }

    scenario = load_scenario_from_dict(data)
    game = initialize_game_from_scenario(scenario, "game123")

    # Expected stern positions relative to bow at (10, 10)
    expected_sterns = {
        "N": (10, 11),  # South
        "NE": (9, 11),  # Southwest
        "E": (9, 10),  # West
        "SE": (9, 9),  # Northwest
        "S": (10, 9),  # North
        "SW": (11, 9),  # Northeast
        "W": (11, 10),  # East
        "NW": (11, 11),  # Southeast
    }

    for facing, (expected_col, expected_row) in expected_sterns.items():
        ship = game.ships[f"ship_{facing.lower()}"]
        assert ship.stern_hex.col == expected_col, f"Failed for {facing} facing (col)"
        assert ship.stern_hex.row == expected_row, f"Failed for {facing} facing (row)"


def test_load_real_scenario_frigate_duel():
    """Test loading the real Frigate Duel scenario."""
    scenario_path = Path(__file__).parent.parent.parent / "scenarios" / "mvp_frigate_duel_v1.json"

    if scenario_path.exists():
        scenario = load_scenario_from_file(scenario_path)
        assert scenario.id == "mvp_frigate_duel_v1"
        assert scenario.name == "Frigate Duel"
        assert len(scenario.ships) == 2
        assert scenario.map.width == 25
        assert scenario.map.height == 20

        # Initialize game to ensure it works
        game = initialize_game_from_scenario(scenario, "test_game")
        assert len(game.ships) == 2


def test_load_real_scenario_crossing_paths():
    """Test loading the real Crossing Paths scenario."""
    scenario_path = Path(__file__).parent.parent.parent / "scenarios" / "mvp_crossing_paths_v1.json"

    if scenario_path.exists():
        scenario = load_scenario_from_file(scenario_path)
        assert scenario.id == "mvp_crossing_paths_v1"
        assert scenario.name == "Crossing Paths"
        assert len(scenario.ships) == 4
        assert scenario.map.width == 18
        assert scenario.map.height == 14

        # Initialize game to ensure it works
        game = initialize_game_from_scenario(scenario, "test_game")
        assert len(game.ships) == 4


def test_load_real_scenario_two_ship_line_battle():
    """Test loading the real Two-Ship Line Battle scenario."""
    scenario_path = (
        Path(__file__).parent.parent.parent / "scenarios" / "mvp_two_ship_line_battle_v1.json"
    )

    if scenario_path.exists():
        scenario = load_scenario_from_file(scenario_path)
        assert scenario.id == "mvp_two_ship_line_battle_v1"
        assert scenario.name == "Two-Ship Line Battle"
        assert len(scenario.ships) == 4
        assert scenario.map.width == 28
        assert scenario.map.height == 18

        # Initialize game to ensure it works
        game = initialize_game_from_scenario(scenario, "test_game")
        assert len(game.ships) == 4
