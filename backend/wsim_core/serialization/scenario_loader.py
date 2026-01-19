"""Scenario loader for loading and validating scenario JSON files."""

import json
from pathlib import Path

from pydantic import ValidationError

from ..models.game import Game
from ..models.hex import HexCoord
from ..models.scenario import Scenario
from ..models.ship import Ship


class ScenarioLoadError(Exception):
    """Raised when scenario loading fails."""

    pass


def load_scenario_from_file(file_path: Path | str) -> Scenario:
    """Load and validate a scenario from a JSON file.

    Args:
        file_path: Path to the scenario JSON file

    Returns:
        Validated Scenario object

    Raises:
        ScenarioLoadError: If file doesn't exist, JSON is invalid, or validation fails
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise ScenarioLoadError(f"Scenario file not found: {file_path}")

    if not file_path.is_file():
        raise ScenarioLoadError(f"Scenario path is not a file: {file_path}")

    try:
        with open(file_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ScenarioLoadError(f"Invalid JSON in scenario file: {e}") from e
    except OSError as e:
        raise ScenarioLoadError(f"Failed to read scenario file: {e}") from e

    try:
        scenario = Scenario.model_validate(data)
    except ValidationError as e:
        raise ScenarioLoadError(f"Scenario validation failed: {e}") from e

    # Additional validations
    try:
        scenario.validate_ship_ids_unique()
        scenario.validate_ships_in_bounds()
    except ValueError as e:
        raise ScenarioLoadError(f"Scenario validation failed: {e}") from e

    return scenario


def load_scenario_from_dict(data: dict) -> Scenario:
    """Load and validate a scenario from a dictionary.

    Args:
        data: Scenario data dictionary

    Returns:
        Validated Scenario object

    Raises:
        ScenarioLoadError: If validation fails
    """
    try:
        scenario = Scenario.model_validate(data)
    except ValidationError as e:
        raise ScenarioLoadError(f"Scenario validation failed: {e}") from e

    # Additional validations
    try:
        scenario.validate_ship_ids_unique()
        scenario.validate_ships_in_bounds()
    except ValueError as e:
        raise ScenarioLoadError(f"Scenario validation failed: {e}") from e

    return scenario


def initialize_game_from_scenario(scenario: Scenario, game_id: str) -> Game:
    """Initialize a new game state from a scenario.

    Args:
        scenario: The scenario to initialize from
        game_id: Unique identifier for the new game

    Returns:
        Initialized Game object
    """
    # Calculate stern hex for each ship based on bow and facing
    ships: dict[str, Ship] = {}
    for scenario_ship in scenario.ships:
        bow_col, bow_row = scenario_ship.start.bow
        bow_hex = HexCoord(col=bow_col, row=bow_row)

        # Calculate stern hex (1 hex behind bow based on facing)
        stern_hex = _calculate_stern_hex(bow_hex, scenario_ship.start.facing)

        ships[scenario_ship.id] = Ship(
            id=scenario_ship.id,
            name=scenario_ship.name,
            side=scenario_ship.side,
            bow_hex=bow_hex,
            stern_hex=stern_hex,
            facing=scenario_ship.start.facing,
            battle_sail_speed=scenario_ship.battle_sail_speed,
            guns_L=scenario_ship.guns.L,
            guns_R=scenario_ship.guns.R,
            carronades_L=scenario_ship.carronades.L,
            carronades_R=scenario_ship.carronades.R,
            hull=scenario_ship.hull,
            rigging=scenario_ship.rigging,
            crew=scenario_ship.crew,
            marines=scenario_ship.marines,
            load_L=scenario_ship.initial_load.L,
            load_R=scenario_ship.initial_load.R,
            fouled=False,
            struck=False,
            turns_without_bow_advance=0,
        )

    return Game(
        id=game_id,
        scenario_id=scenario.id,
        turn_number=1,
        map_width=scenario.map.width,
        map_height=scenario.map.height,
        wind_direction=scenario.wind.direction,
        ships=ships,
        turn_limit=scenario.turn_limit,
        victory_condition=scenario.victory.type,
    )


def _calculate_stern_hex(bow_hex: HexCoord, facing: str) -> HexCoord:
    """Calculate stern hex position based on bow hex and facing.

    The stern is 1 hex behind the bow in the opposite direction of facing.

    Args:
        bow_hex: The bow hex position
        facing: The ship's facing direction

    Returns:
        The stern hex position
    """
    # Offset map for hex directions (assuming offset coordinates)
    # In a hex grid, each direction has a different offset
    # We'll use the opposite direction from facing
    offsets = {
        "N": (0, 1),  # Stern is to the South
        "NE": (-1, 1),  # Stern is to the Southwest
        "E": (-1, 0),  # Stern is to the West
        "SE": (-1, -1),  # Stern is to the Northwest
        "S": (0, -1),  # Stern is to the North
        "SW": (1, -1),  # Stern is to the Northeast
        "W": (1, 0),  # Stern is to the East
        "NW": (1, 1),  # Stern is to the Southeast
    }

    offset = offsets[facing]
    return HexCoord(col=bow_hex.col + offset[0], row=bow_hex.row + offset[1])
