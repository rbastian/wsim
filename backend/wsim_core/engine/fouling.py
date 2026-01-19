"""Fouling system for ship collisions.

This module handles fouling checks after collisions and manages fouled status.
In WS&IM, when ships collide, they may become fouled (tangled rigging/spars).
Fouled ships have restricted movement until they unfoul.
"""

from pydantic import BaseModel, Field

from ..models.common import GamePhase
from ..models.events import EventLogEntry
from ..models.ship import Ship
from .rng import RNG


class FoulingResult(BaseModel):
    """Result of a fouling check."""

    ship_ids: list[str] = Field(description="Ship IDs involved in fouling check")
    fouled: bool = Field(description="Whether ships become fouled")
    roll: int = Field(description="Die roll for fouling check")
    events: list[EventLogEntry] = Field(
        default_factory=list, description="Event log entries for fouling check"
    )


def check_fouling(
    ship_ids: list[str],
    ships: dict[str, Ship],
    rng: RNG,
    turn_number: int,
) -> FoulingResult:
    """Check if ships become fouled after a collision.

    Fouling rules (simplified MVP version):
    - Roll 1d6 for fouling check
    - On 1-3: Ships become fouled
    - On 4-6: Ships do not become fouled

    Args:
        ship_ids: IDs of ships involved in collision
        ships: Dictionary of all ships
        rng: Random number generator
        turn_number: Current turn number for event logging

    Returns:
        FoulingResult with roll outcome and updated ship status
    """
    if len(ship_ids) < 2:
        # No fouling if fewer than 2 ships
        return FoulingResult(ship_ids=ship_ids, fouled=False, roll=0)

    # Roll for fouling
    roll = rng.roll_d6()
    fouled = roll <= 3

    # Get ship names for event logging
    ship_names = [ships[sid].name for sid in ship_ids]

    # Create event log entry
    event = EventLogEntry(
        turn_number=turn_number,
        phase=GamePhase.MOVEMENT,
        event_type="fouling_check",
        summary=(
            f"Fouling check for {', '.join(ship_names)}: "
            f"rolled {roll}. "
            f"{'Ships become fouled!' if fouled else 'Ships avoid fouling.'}"
        ),
        metadata={
            "ship_ids": ship_ids,
            "roll": roll,
            "fouled": fouled,
        },
    )

    return FoulingResult(ship_ids=ship_ids, fouled=fouled, roll=roll, events=[event])


def apply_fouling(
    ships: dict[str, Ship],
    fouling_result: FoulingResult,
) -> dict[str, Ship]:
    """Apply fouling status to ships based on fouling check result.

    Args:
        ships: Dictionary of all ships
        fouling_result: Result of fouling check

    Returns:
        Updated ships dictionary with fouling status applied
    """
    if not fouling_result.fouled:
        # No fouling occurred
        return ships

    updated_ships = ships.copy()

    # Apply fouled status to all involved ships
    for ship_id in fouling_result.ship_ids:
        if ship_id in updated_ships:
            ship = updated_ships[ship_id]
            updated_ships[ship_id] = ship.model_copy(update={"fouled": True})

    return updated_ships


def check_and_apply_fouling(
    ship_ids: list[str],
    ships: dict[str, Ship],
    rng: RNG,
    turn_number: int,
) -> tuple[dict[str, Ship], FoulingResult]:
    """Check for fouling and apply results to ships.

    Convenience function that combines check_fouling and apply_fouling.

    Args:
        ship_ids: IDs of ships involved in collision
        ships: Dictionary of all ships
        rng: Random number generator
        turn_number: Current turn number for event logging

    Returns:
        Tuple of (updated ships dictionary, fouling result)
    """
    fouling_result = check_fouling(ship_ids=ship_ids, ships=ships, rng=rng, turn_number=turn_number)

    updated_ships = apply_fouling(ships=ships, fouling_result=fouling_result)

    return updated_ships, fouling_result
