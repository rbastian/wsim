"""Drift system for ships without forward movement.

Implements the drift rule: ships that fail to advance their bow hex for 2 consecutive
turns must drift 1 hex downwind.
"""

from pydantic import BaseModel, Field

from ..models.common import Facing, GamePhase, WindDirection
from ..models.events import EventLogEntry
from ..models.hex import HexCoord
from ..models.ship import Ship


class DriftResult(BaseModel):
    """Result of checking and applying drift to ships."""

    drifted_ships: dict[str, tuple[HexCoord, HexCoord]] = Field(
        description="Map of ship_id to (new_bow, new_stern) for ships that drifted"
    )
    events: list[EventLogEntry] = Field(default_factory=list, description="Drift events")


def get_downwind_direction(wind_direction: WindDirection) -> WindDirection:
    """Get the downwind direction (opposite of wind direction).

    Args:
        wind_direction: Current wind direction (where wind comes FROM)

    Returns:
        Direction wind is blowing TO (downwind)
    """
    opposite_map = {
        WindDirection.N: WindDirection.S,
        WindDirection.NE: WindDirection.SW,
        WindDirection.E: WindDirection.W,
        WindDirection.SE: WindDirection.NW,
        WindDirection.S: WindDirection.N,
        WindDirection.SW: WindDirection.NE,
        WindDirection.W: WindDirection.E,
        WindDirection.NW: WindDirection.SE,
    }
    return opposite_map[wind_direction]


def update_drift_tracking(
    ships: dict[str, Ship], movement_result: dict[str, bool]
) -> dict[str, Ship]:
    """Update drift tracking counters based on movement results.

    Increments turns_without_bow_advance for ships that didn't advance their bow,
    resets it to 0 for ships that did advance.

    Args:
        ships: Dictionary of all ships by ship_id
        movement_result: Map of ship_id to whether bow advanced this turn

    Returns:
        Updated ships dictionary with new drift tracking values
    """
    updated_ships = {}

    for ship_id, ship in ships.items():
        bow_advanced = movement_result.get(ship_id, False)

        if bow_advanced:
            # Reset counter if bow advanced
            updated_ships[ship_id] = ship.model_copy(update={"turns_without_bow_advance": 0})
        else:
            # Increment counter if bow did not advance
            updated_ships[ship_id] = ship.model_copy(
                update={"turns_without_bow_advance": ship.turns_without_bow_advance + 1}
            )

    return updated_ships


def apply_drift(
    ships: dict[str, Ship],
    wind_direction: WindDirection,
    map_width: int,
    map_height: int,
    turn_number: int,
) -> tuple[dict[str, Ship], DriftResult]:
    """Apply drift to ships that haven't advanced for 2 turns.

    Ships with turns_without_bow_advance >= 2 drift 1 hex downwind.
    Both bow and stern move in the same direction.

    Args:
        ships: Dictionary of all ships by ship_id
        wind_direction: Current wind direction
        map_width: Map width for bounds checking
        map_height: Map height for bounds checking
        turn_number: Current turn number for event logging

    Returns:
        Tuple of (updated ships dict, drift result with events)
    """
    downwind = get_downwind_direction(wind_direction)
    # Convert WindDirection to Facing for hex geometry calculations
    downwind_facing = Facing(downwind.value)
    updated_ships = {}
    drifted_ships = {}
    events = []

    for ship_id, ship in ships.items():
        # Check if ship needs to drift
        if ship.turns_without_bow_advance >= 2:
            # Calculate what the new positions would be (1 hex downwind)
            # We need to check bounds before calling get_adjacent_hex since
            # HexCoord validation will fail on negative values

            # Calculate offsets manually to check bounds first
            col = ship.bow_hex.col
            row = ship.bow_hex.row
            is_odd_col = col % 2 == 1

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

            col_offset, row_offset_even, row_offset_odd = direction_offsets[downwind_facing]
            row_offset = row_offset_odd if is_odd_col else row_offset_even

            new_bow_col = col + col_offset
            new_bow_row = row + row_offset

            # Same for stern
            stern_col = ship.stern_hex.col
            stern_row = ship.stern_hex.row
            stern_is_odd_col = stern_col % 2 == 1
            stern_row_offset = row_offset_odd if stern_is_odd_col else row_offset_even

            new_stern_col = stern_col + col_offset
            new_stern_row = stern_row + stern_row_offset

            # Validate bounds before creating HexCoord objects
            if (
                new_bow_col < 0
                or new_bow_col >= map_width
                or new_bow_row < 0
                or new_bow_row >= map_height
                or new_stern_col < 0
                or new_stern_col >= map_width
                or new_stern_row < 0
                or new_stern_row >= map_height
            ):
                # Skip drift if it would go out of bounds
                updated_ships[ship_id] = ship
                events.append(
                    EventLogEntry(
                        turn_number=turn_number,
                        phase=GamePhase.MOVEMENT,
                        event_type="drift_blocked",
                        summary=(
                            f"Ship {ship.name} ({ship_id}) cannot drift - would go out of bounds"
                        ),
                        metadata={
                            "ship_id": ship_id,
                            "ship_name": ship.name,
                            "wind_direction": wind_direction.value,
                            "reason": "out_of_bounds",
                        },
                    )
                )
                continue

            # Now safe to create HexCoord objects
            new_bow = HexCoord(col=new_bow_col, row=new_bow_row)
            new_stern = HexCoord(col=new_stern_col, row=new_stern_row)

            # Apply drift
            updated_ships[ship_id] = ship.model_copy(
                update={
                    "bow_hex": new_bow,
                    "stern_hex": new_stern,
                    "turns_without_bow_advance": 0,  # Reset counter after drift
                }
            )
            drifted_ships[ship_id] = (new_bow, new_stern)

            # Create drift event
            events.append(
                EventLogEntry(
                    turn_number=turn_number,
                    phase=GamePhase.MOVEMENT,
                    event_type="drift",
                    summary=(
                        f"Ship {ship.name} ({ship_id}) drifted 1 hex {downwind.value} "
                        f"(no bow advance for {ship.turns_without_bow_advance} turns)"
                    ),
                    metadata={
                        "ship_id": ship_id,
                        "ship_name": ship.name,
                        "old_bow": {"col": ship.bow_hex.col, "row": ship.bow_hex.row},
                        "new_bow": {"col": new_bow.col, "row": new_bow.row},
                        "old_stern": {"col": ship.stern_hex.col, "row": ship.stern_hex.row},
                        "new_stern": {"col": new_stern.col, "row": new_stern.row},
                        "wind_direction": wind_direction.value,
                        "drift_direction": downwind.value,
                        "turns_without_advance": ship.turns_without_bow_advance,
                    },
                )
            )
        else:
            # No drift needed
            updated_ships[ship_id] = ship

    result = DriftResult(drifted_ships=drifted_ships, events=events)
    return updated_ships, result


def check_and_apply_drift(
    ships: dict[str, Ship],
    movement_result: dict[str, bool],
    wind_direction: WindDirection,
    map_width: int,
    map_height: int,
    turn_number: int,
) -> tuple[dict[str, Ship], DriftResult]:
    """Update drift tracking and apply drift in one step.

    This is a convenience function that combines drift tracking updates
    with drift application.

    Args:
        ships: Dictionary of all ships by ship_id
        movement_result: Map of ship_id to whether bow advanced this turn
        wind_direction: Current wind direction
        map_width: Map width for bounds checking
        map_height: Map height for bounds checking
        turn_number: Current turn number for event logging

    Returns:
        Tuple of (updated ships dict, drift result with events)
    """
    # First update drift tracking based on movement
    tracked_ships = update_drift_tracking(ships, movement_result)

    # Then apply drift to ships that need it
    return apply_drift(tracked_ships, wind_direction, map_width, map_height, turn_number)
