"""Broadside reload system.

This module implements reload logic for ship broadsides:
- Tracking which broadsides have been fired
- Marking broadsides as unloaded after firing
- Reloading broadsides during the reload phase
- Validating load states before firing
"""

from pydantic import BaseModel, Field

from ..models.common import Broadside, GamePhase, LoadState
from ..models.events import EventLogEntry
from ..models.ship import Ship


class ReloadResult(BaseModel):
    """Result of reloading a ship's broadsides.

    Attributes:
        ship_id: ID of ship that was reloaded
        left_reloaded: Whether left broadside was reloaded
        right_reloaded: Whether right broadside was reloaded
        left_final_state: Final load state of left broadside
        right_final_state: Final load state of right broadside
    """

    ship_id: str = Field(description="Ship identifier")
    left_reloaded: bool = Field(description="Whether left broadside was reloaded")
    right_reloaded: bool = Field(description="Whether right broadside was reloaded")
    left_final_state: LoadState = Field(description="Final load state of left broadside")
    right_final_state: LoadState = Field(description="Final load state of right broadside")


def mark_broadside_fired(ship: Ship, broadside: Broadside) -> None:
    """Mark a broadside as fired (unloaded).

    This should be called immediately after a broadside fires during combat phase.

    Args:
        ship: Ship whose broadside was fired
        broadside: Which broadside was fired (L or R)
    """
    if broadside == Broadside.L:
        ship.load_L = LoadState.EMPTY
    else:
        ship.load_R = LoadState.EMPTY


def reload_broadside(ship: Ship, broadside: Broadside) -> bool:
    """Reload a single broadside.

    Args:
        ship: Ship to reload
        broadside: Which broadside to reload (L or R)

    Returns:
        True if broadside was reloaded, False if already loaded
    """
    current_state = ship.load_L if broadside == Broadside.L else ship.load_R

    # If already loaded, nothing to do
    if current_state != LoadState.EMPTY:
        return False

    # Reload with roundshot (MVP only uses roundshot)
    if broadside == Broadside.L:
        ship.load_L = LoadState.ROUNDSHOT
    else:
        ship.load_R = LoadState.ROUNDSHOT

    return True


def reload_ship(ship: Ship) -> ReloadResult:
    """Reload all empty broadsides on a ship.

    Args:
        ship: Ship to reload

    Returns:
        ReloadResult with details of what was reloaded
    """
    left_reloaded = reload_broadside(ship, Broadside.L)
    right_reloaded = reload_broadside(ship, Broadside.R)

    return ReloadResult(
        ship_id=ship.id,
        left_reloaded=left_reloaded,
        right_reloaded=right_reloaded,
        left_final_state=ship.load_L,
        right_final_state=ship.load_R,
    )


def reload_all_ships(ships: list[Ship], turn_number: int) -> list[ReloadResult]:
    """Reload all ships that have empty broadsides.

    Args:
        ships: List of ships to reload
        turn_number: Current turn number (for event logging)

    Returns:
        List of ReloadResult for each ship
    """
    results = []
    for ship in ships:
        # Skip struck ships
        if ship.struck:
            continue

        result = reload_ship(ship)
        results.append(result)

    return results


def create_reload_event(
    result: ReloadResult,
    turn_number: int,
    ship_name: str,
) -> EventLogEntry:
    """Create an event log entry for a reload operation.

    Args:
        result: Reload result
        turn_number: Current turn number
        ship_name: Name of ship for summary

    Returns:
        EventLogEntry documenting the reload
    """
    reloaded = []
    if result.left_reloaded:
        reloaded.append("L")
    if result.right_reloaded:
        reloaded.append("R")

    if not reloaded:
        summary = f"{ship_name}: No reloading needed (all broadsides loaded)"
    else:
        summary = f"{ship_name}: Reloaded broadside(s) {', '.join(reloaded)} with roundshot"

    return EventLogEntry(
        turn_number=turn_number,
        phase=GamePhase.RELOAD,
        event_type="reload",
        summary=summary,
        metadata={
            "ship_id": result.ship_id,
            "ship_name": ship_name,
            "left_reloaded": result.left_reloaded,
            "right_reloaded": result.right_reloaded,
            "left_final_state": result.left_final_state.value,
            "right_final_state": result.right_final_state.value,
        },
    )


def is_broadside_loaded(ship: Ship, broadside: Broadside) -> bool:
    """Check if a broadside is loaded and ready to fire.

    Args:
        ship: Ship to check
        broadside: Which broadside to check

    Returns:
        True if broadside is loaded (not EMPTY)
    """
    load_state = ship.load_L if broadside == Broadside.L else ship.load_R
    return load_state != LoadState.EMPTY


def can_reload_ship(ship: Ship) -> bool:
    """Check if a ship can participate in reload phase.

    A ship can reload if:
    - It is not struck
    - It has at least one empty broadside

    Args:
        ship: Ship to check

    Returns:
        True if ship can reload
    """
    if ship.struck:
        return False

    return ship.load_L == LoadState.EMPTY or ship.load_R == LoadState.EMPTY
