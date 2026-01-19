"""Movement execution engine for simultaneous ship movement.

This module executes parsed movement actions step-by-step for all ships
simultaneously, handling hex geometry, position updates, and movement tracking.
"""

from pydantic import BaseModel, Field

from ..models.common import Facing
from ..models.hex import HexCoord
from ..models.ship import Ship
from .movement_parser import MovementAction, MovementActionType, ParsedMovement


class MovementExecutionError(Exception):
    """Raised when movement execution fails."""

    pass


class ShipMovementState(BaseModel):
    """Tracks the movement state for a single ship during execution."""

    ship_id: str = Field(description="Ship identifier")
    parsed_movement: ParsedMovement = Field(description="Parsed movement for this ship")
    current_action_index: int = Field(default=0, ge=0, description="Current action being executed")
    hexes_moved_forward: int = Field(default=0, ge=0, description="Total hexes moved forward")
    bow_advanced: bool = Field(default=False, description="Whether bow hex changed this turn")
    completed: bool = Field(default=False, description="Whether all actions are complete")

    def get_next_action(self) -> MovementAction | None:
        """Get the next action to execute, or None if completed."""
        if self.current_action_index >= len(self.parsed_movement.actions):
            return None
        return self.parsed_movement.actions[self.current_action_index]

    def advance_action(self) -> None:
        """Move to the next action in the sequence."""
        self.current_action_index += 1
        if self.current_action_index >= len(self.parsed_movement.actions):
            self.completed = True


class MovementExecutionResult(BaseModel):
    """Result of executing movement for all ships."""

    ships_moved: dict[str, bool] = Field(
        description="Map of ship_id to whether bow advanced this turn"
    )
    total_actions_executed: int = Field(default=0, ge=0, description="Total actions executed")


# Hex geometry constants and utilities
# Using offset coordinates (odd-q vertical layout)


def turn_left(facing: Facing) -> Facing:
    """Rotate facing 60 degrees counter-clockwise (left).

    In hex grids, turns are 60 degrees. With 8 compass directions,
    a full 360-degree rotation takes 6 steps (60 * 6 = 360).
    """
    rotation_map = {
        Facing.N: Facing.NW,
        Facing.NE: Facing.N,
        Facing.E: Facing.NE,
        Facing.SE: Facing.E,
        Facing.S: Facing.SE,
        Facing.SW: Facing.S,
        Facing.W: Facing.SW,
        Facing.NW: Facing.W,
    }
    return rotation_map[facing]


def turn_right(facing: Facing) -> Facing:
    """Rotate facing 60 degrees clockwise (right).

    In hex grids, turns are 60 degrees. With 8 compass directions,
    a full 360-degree rotation takes 6 steps (60 * 6 = 360).
    """
    rotation_map = {
        Facing.N: Facing.NE,
        Facing.NE: Facing.E,
        Facing.E: Facing.SE,
        Facing.SE: Facing.S,
        Facing.S: Facing.SW,
        Facing.SW: Facing.W,
        Facing.W: Facing.NW,
        Facing.NW: Facing.N,
    }
    return rotation_map[facing]


def get_adjacent_hex(hex_coord: HexCoord, direction: Facing) -> HexCoord:
    """Get the adjacent hex in the given direction.

    Uses odd-q vertical layout hex grid geometry.
    In odd-q:
    - Odd columns (col % 2 == 1) are shifted down by 0.5 row
    - Even columns (col % 2 == 0) are aligned

    Args:
        hex_coord: Starting hex coordinate
        direction: Direction to move

    Returns:
        The adjacent hex coordinate in that direction
    """
    col, row = hex_coord.col, hex_coord.row
    is_odd_col = col % 2 == 1

    # Direction offsets for odd-q vertical layout
    # Format: (col_offset, row_offset_even_col, row_offset_odd_col)
    direction_offsets = {
        Facing.N: (0, -1, -1),
        Facing.NE: (1, -1, 0),
        Facing.SE: (1, 0, 1),
        Facing.S: (0, 1, 1),
        Facing.SW: (-1, 0, 1),
        Facing.NW: (-1, -1, 0),
        # Cardinal directions map to their closest hex neighbor
        Facing.E: (1, 0, 0),  # Directly east
        Facing.W: (-1, 0, 0),  # Directly west
    }

    col_offset, row_offset_even, row_offset_odd = direction_offsets[direction]
    row_offset = row_offset_odd if is_odd_col else row_offset_even

    return HexCoord(col=col + col_offset, row=row + row_offset)


def calculate_stern_from_bow(bow: HexCoord, facing: Facing) -> HexCoord:
    """Calculate stern hex based on bow hex and facing.

    The stern is always one hex behind the bow in the opposite direction.

    Args:
        bow: Bow hex coordinate
        facing: Ship facing direction

    Returns:
        Stern hex coordinate
    """
    # Get the opposite direction (180 degrees)
    opposite_facing_map = {
        Facing.N: Facing.S,
        Facing.NE: Facing.SW,
        Facing.E: Facing.W,
        Facing.SE: Facing.NW,
        Facing.S: Facing.N,
        Facing.SW: Facing.NE,
        Facing.W: Facing.E,
        Facing.NW: Facing.SE,
    }

    opposite_direction = opposite_facing_map[facing]
    return get_adjacent_hex(bow, opposite_direction)


def execute_ship_turn(ship: Ship, turn_direction: MovementActionType) -> Ship:
    """Execute a turn action for a ship.

    Args:
        ship: The ship to turn
        turn_direction: TURN_LEFT or TURN_RIGHT

    Returns:
        Updated ship with new facing (position unchanged)

    Raises:
        MovementExecutionError: If turn_direction is invalid
    """
    if turn_direction == MovementActionType.TURN_LEFT:
        new_facing = turn_left(ship.facing)
    elif turn_direction == MovementActionType.TURN_RIGHT:
        new_facing = turn_right(ship.facing)
    else:
        raise MovementExecutionError(
            f"Invalid turn direction: {turn_direction}. Must be TURN_LEFT or TURN_RIGHT"
        )

    # Update ship facing and recalculate stern position
    new_stern = calculate_stern_from_bow(ship.bow_hex, new_facing)

    return ship.model_copy(update={"facing": new_facing, "stern_hex": new_stern})


def execute_ship_forward_movement(
    ship: Ship, distance: int, map_width: int, map_height: int
) -> Ship:
    """Execute forward movement for a ship.

    Args:
        ship: The ship to move
        distance: Number of hexes to move forward
        map_width: Map width for bounds checking
        map_height: Map height for bounds checking

    Returns:
        Updated ship with new position

    Raises:
        MovementExecutionError: If movement would go out of bounds
    """
    if distance <= 0:
        return ship

    # Calculate new bow position step by step, checking bounds at each step
    new_bow_col = ship.bow_hex.col
    new_bow_row = ship.bow_hex.row

    for _ in range(distance):
        # Calculate next position
        is_odd_col = new_bow_col % 2 == 1

        direction_offsets = {
            Facing.N: (0, -1, -1),
            Facing.NE: (1, -1, 0),
            Facing.SE: (1, 0, 1),
            Facing.S: (0, 1, 1),
            Facing.SW: (-1, 0, 1),
            Facing.NW: (-1, -1, 0),
            Facing.E: (1, 0, 0),
            Facing.W: (-1, 0, 0),
        }

        col_offset, row_offset_even, row_offset_odd = direction_offsets[ship.facing]
        row_offset = row_offset_odd if is_odd_col else row_offset_even

        new_bow_col += col_offset
        new_bow_row += row_offset

        # Check bounds before continuing
        if (
            new_bow_col < 0
            or new_bow_col >= map_width
            or new_bow_row < 0
            or new_bow_row >= map_height
        ):
            raise MovementExecutionError(
                f"Ship {ship.id} movement would go out of bounds: "
                f"attempted position ({new_bow_col}, {new_bow_row}), "
                f"map size ({map_width}, {map_height})"
            )

    # Create new bow position (validated to be in bounds)
    new_bow = HexCoord(col=new_bow_col, row=new_bow_row)

    # Calculate new stern position
    new_stern = calculate_stern_from_bow(new_bow, ship.facing)

    return ship.model_copy(update={"bow_hex": new_bow, "stern_hex": new_stern})


def execute_simultaneous_movement(
    ships: dict[str, Ship],
    movements: dict[str, ParsedMovement],
    map_width: int,
    map_height: int,
) -> tuple[dict[str, Ship], MovementExecutionResult]:
    """Execute simultaneous movement for all ships.

    Processes all ship movements step-by-step in parallel. Each step, all ships
    execute their next action simultaneously before moving to the next step.

    Args:
        ships: Dictionary of all ships by ship_id
        movements: Dictionary of parsed movements by ship_id
        map_width: Map width for bounds checking
        map_height: Map height for bounds checking

    Returns:
        Tuple of (updated ships dict, execution result)

    Raises:
        MovementExecutionError: If any ship's movement is invalid
    """
    # Initialize movement state for each ship
    movement_states: dict[str, ShipMovementState] = {}
    for ship_id, parsed_movement in movements.items():
        if ship_id not in ships:
            raise MovementExecutionError(f"Ship {ship_id} not found in game")

        movement_states[ship_id] = ShipMovementState(
            ship_id=ship_id, parsed_movement=parsed_movement
        )

    # Create working copy of ships
    updated_ships = {ship_id: ship.model_copy(deep=True) for ship_id, ship in ships.items()}

    total_actions = 0

    # Execute movement step-by-step until all ships complete
    while not all(state.completed for state in movement_states.values()):
        # Process each ship's next action
        for ship_id, state in movement_states.items():
            if state.completed:
                continue

            action = state.get_next_action()
            if action is None:
                state.completed = True
                continue

            ship = updated_ships[ship_id]

            # Execute the action based on type
            if action.action_type == MovementActionType.NO_MOVEMENT:
                # No movement - mark complete
                state.completed = True

            elif action.action_type in (
                MovementActionType.TURN_LEFT,
                MovementActionType.TURN_RIGHT,
            ):
                # Execute turn
                updated_ships[ship_id] = execute_ship_turn(ship, action.action_type)
                state.advance_action()
                total_actions += 1

            elif action.action_type == MovementActionType.MOVE_FORWARD:
                # Validate movement allowance before executing
                new_distance = state.hexes_moved_forward + action.distance
                if new_distance > ship.battle_sail_speed:
                    raise MovementExecutionError(
                        f"Ship {ship_id} movement exceeds battle sail speed: "
                        f"attempted {new_distance} hexes, allowed {ship.battle_sail_speed}"
                    )

                # Track original bow position
                original_bow = ship.bow_hex

                # Execute forward movement
                updated_ships[ship_id] = execute_ship_forward_movement(
                    ship, action.distance, map_width, map_height
                )

                # Check if bow advanced
                if updated_ships[ship_id].bow_hex != original_bow:
                    state.bow_advanced = True

                state.hexes_moved_forward += action.distance
                state.advance_action()
                total_actions += 1

    # Build result
    ships_moved = {ship_id: state.bow_advanced for ship_id, state in movement_states.items()}

    result = MovementExecutionResult(ships_moved=ships_moved, total_actions_executed=total_actions)

    return updated_ships, result
