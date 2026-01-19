"""Collision detection and resolution for simultaneous ship movement.

This module handles detecting when ships enter the same hex during movement
and resolving which ship occupies the hex, truncating voluntary movement
as appropriate.
"""

from pydantic import BaseModel, Field

from ..models.common import GamePhase
from ..models.events import EventLogEntry
from ..models.hex import HexCoord
from ..models.ship import Ship
from .fouling import check_and_apply_fouling
from .rng import RNG


class CollisionDetectionError(Exception):
    """Raised when collision detection encounters an error."""

    pass


class CollisionResolution(BaseModel):
    """Result of resolving a collision between ships."""

    collision_hex: HexCoord = Field(description="Hex where collision occurred")
    ship_ids_involved: list[str] = Field(description="All ships involved in collision")
    occupying_ship_id: str = Field(description="Ship that ends up occupying the hex")
    displaced_ship_ids: list[str] = Field(
        description="Ships that must be moved back to previous position"
    )
    truncate_movement: bool = Field(
        default=True, description="Whether to end voluntary movement for involved ships"
    )


class CollisionResult(BaseModel):
    """Result of collision detection and resolution for a movement step."""

    collisions: list[CollisionResolution] = Field(
        default_factory=list, description="All collisions detected this step"
    )
    events: list[EventLogEntry] = Field(
        default_factory=list, description="Event log entries for collisions"
    )


def get_ship_hexes(ship: Ship) -> set[HexCoord]:
    """Get all hexes occupied by a ship (bow and stern).

    Args:
        ship: The ship

    Returns:
        Set of hex coordinates occupied by the ship
    """
    return {ship.bow_hex, ship.stern_hex}


def detect_hex_occupancy(ships: dict[str, Ship]) -> dict[HexCoord, list[str]]:
    """Build a map of which ships occupy which hexes.

    Args:
        ships: Dictionary of all ships by ship_id

    Returns:
        Dictionary mapping hex coordinates to list of ship IDs occupying that hex
    """
    hex_to_ships: dict[HexCoord, list[str]] = {}

    for ship_id, ship in ships.items():
        for hex_coord in get_ship_hexes(ship):
            if hex_coord not in hex_to_ships:
                hex_to_ships[hex_coord] = []
            hex_to_ships[hex_coord].append(ship_id)

    return hex_to_ships


def detect_collisions(
    ships_before: dict[str, Ship],
    ships_after: dict[str, Ship],
) -> list[tuple[HexCoord, list[str]]]:
    """Detect collisions by comparing ship positions before and after a movement step.

    A collision occurs when multiple ships occupy the same hex after movement.

    Args:
        ships_before: Ship positions before the movement step
        ships_after: Ship positions after the movement step

    Returns:
        List of (collision_hex, ship_ids) tuples for each collision detected
    """
    # Check occupancy after movement
    hex_occupancy = detect_hex_occupancy(ships_after)

    # Find hexes with multiple ships
    collisions: list[tuple[HexCoord, list[str]]] = []

    for hex_coord, ship_ids in hex_occupancy.items():
        if len(ship_ids) > 1:
            collisions.append((hex_coord, ship_ids))

    return collisions


def resolve_collision(
    collision_hex: HexCoord,
    ship_ids: list[str],
    ships_before: dict[str, Ship],
    ships_after: dict[str, Ship],
    rng: RNG,
    turn_number: int,
) -> tuple[CollisionResolution, EventLogEntry]:
    """Resolve a collision by determining which ship occupies the hex.

    Resolution logic:
    1. If only one ship moved into the hex, it occupies the hex
    2. If multiple ships moved into the hex, randomly determine occupant
    3. Displaced ships are moved back to their previous position
    4. All involved ships have their movement truncated

    Args:
        collision_hex: The hex where collision occurred
        ship_ids: IDs of all ships involved in the collision
        ships_before: Ship positions before movement
        ships_after: Ship positions after movement
        rng: Random number generator for tie-breaking
        turn_number: Current turn number for event logging

    Returns:
        Tuple of (collision resolution, event log entry)

    Raises:
        CollisionDetectionError: If collision resolution fails
    """
    if len(ship_ids) < 2:
        raise CollisionDetectionError(
            f"resolve_collision called with fewer than 2 ships: {ship_ids}"
        )

    # Determine which ships moved into this hex vs already occupied it
    ships_that_moved_here = []
    ships_already_here = []

    for ship_id in ship_ids:
        ship_before = ships_before[ship_id]

        # Check if this ship occupied this hex before movement
        if collision_hex in get_ship_hexes(ship_before):
            ships_already_here.append(ship_id)
        else:
            ships_that_moved_here.append(ship_id)

    # Determine occupant based on who was here first
    if len(ships_already_here) == 1 and len(ships_that_moved_here) >= 1:
        # Ship that was already here stays
        occupying_ship_id = ships_already_here[0]
        displaced_ship_ids = ships_that_moved_here
        resolution_method = "stationary_priority"

    elif len(ships_that_moved_here) >= 2 and len(ships_already_here) == 0:
        # Multiple ships moved into same hex - random selection
        # Roll die to determine which ship occupies hex
        roll = rng.roll_d6()
        selected_index = roll % len(ships_that_moved_here)
        occupying_ship_id = ships_that_moved_here[selected_index]
        displaced_ship_ids = [sid for sid in ships_that_moved_here if sid != occupying_ship_id]
        resolution_method = f"random_selection_d6={roll}"

    elif len(ships_already_here) >= 2:
        # Multiple ships were already in this hex - this shouldn't happen
        # but handle it by picking first one
        occupying_ship_id = ships_already_here[0]
        displaced_ship_ids = ships_already_here[1:] + ships_that_moved_here
        resolution_method = "multiple_stationary_fallback"

    else:
        # Fallback - shouldn't reach here but handle defensively
        occupying_ship_id = ship_ids[0]
        displaced_ship_ids = ship_ids[1:]
        resolution_method = "fallback"

    # Create collision resolution
    resolution = CollisionResolution(
        collision_hex=collision_hex,
        ship_ids_involved=ship_ids,
        occupying_ship_id=occupying_ship_id,
        displaced_ship_ids=displaced_ship_ids,
        truncate_movement=True,
    )

    # Create event log entry
    ship_names = [ships_after[sid].name for sid in ship_ids]
    occupying_ship_name = ships_after[occupying_ship_id].name

    event = EventLogEntry(
        turn_number=turn_number,
        phase=GamePhase.MOVEMENT,
        event_type="collision",
        summary=(
            f"Collision at {collision_hex}: ships {', '.join(ship_names)}. "
            f"{occupying_ship_name} occupies hex, others displaced. "
            f"Voluntary movement ends for all involved ships."
        ),
        metadata={
            "collision_hex": {"col": collision_hex.col, "row": collision_hex.row},
            "ship_ids_involved": ship_ids,
            "occupying_ship_id": occupying_ship_id,
            "displaced_ship_ids": displaced_ship_ids,
            "resolution_method": resolution_method,
        },
    )

    return resolution, event


def apply_collision_resolution(
    ships: dict[str, Ship],
    ships_before: dict[str, Ship],
    resolution: CollisionResolution,
) -> dict[str, Ship]:
    """Apply collision resolution by moving displaced ships back to previous positions.

    Args:
        ships: Current ship positions (after movement)
        ships_before: Ship positions before movement (to restore displaced ships)
        resolution: Collision resolution to apply

    Returns:
        Updated ships dictionary with displaced ships moved back
    """
    updated_ships = ships.copy()

    # Move displaced ships back to their previous positions
    for ship_id in resolution.displaced_ship_ids:
        if ship_id in ships_before:
            # Restore ship to previous position
            previous_ship = ships_before[ship_id]
            updated_ships[ship_id] = previous_ship.model_copy(deep=True)

    return updated_ships


def detect_and_resolve_collisions(
    ships_before: dict[str, Ship],
    ships_after: dict[str, Ship],
    rng: RNG,
    turn_number: int,
) -> tuple[dict[str, Ship], CollisionResult]:
    """Detect and resolve all collisions from a movement step.

    This includes:
    1. Detecting collisions
    2. Resolving which ship occupies the collision hex
    3. Checking for fouling between colliding ships
    4. Applying fouled status if fouling occurs

    Args:
        ships_before: Ship positions before movement step
        ships_after: Ship positions after movement step
        rng: Random number generator for collision resolution
        turn_number: Current turn number for event logging

    Returns:
        Tuple of (resolved ship positions, collision result)
    """
    # Detect collisions
    collisions = detect_collisions(ships_before, ships_after)

    if not collisions:
        # No collisions
        return ships_after, CollisionResult()

    # Resolve each collision
    collision_resolutions: list[CollisionResolution] = []
    events: list[EventLogEntry] = []
    resolved_ships = ships_after.copy()

    for collision_hex, ship_ids in collisions:
        resolution, event = resolve_collision(
            collision_hex=collision_hex,
            ship_ids=ship_ids,
            ships_before=ships_before,
            ships_after=ships_after,
            rng=rng,
            turn_number=turn_number,
        )

        collision_resolutions.append(resolution)
        events.append(event)

        # Apply resolution (move displaced ships back)
        resolved_ships = apply_collision_resolution(
            ships=resolved_ships, ships_before=ships_before, resolution=resolution
        )

        # Check for fouling between colliding ships
        resolved_ships, fouling_result = check_and_apply_fouling(
            ship_ids=ship_ids, ships=resolved_ships, rng=rng, turn_number=turn_number
        )

        # Add fouling events to event log
        events.extend(fouling_result.events)

    result = CollisionResult(collisions=collision_resolutions, events=events)

    return resolved_ships, result
