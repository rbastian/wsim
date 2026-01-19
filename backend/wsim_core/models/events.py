"""Event log models for audit trail."""

from typing import Any

from pydantic import BaseModel, Field

from .common import GamePhase


class DiceRoll(BaseModel):
    """Record of a dice roll."""

    num_dice: int = Field(ge=1, description="Number of dice rolled")
    die_type: int = Field(ge=2, description="Type of die (e.g., 6 for d6)")
    rolls: list[int] = Field(description="Individual die results")
    total: int = Field(description="Sum of all dice")


class EventLogEntry(BaseModel):
    """A single event in the game log.

    Records game actions, dice rolls, and rule resolutions for debugging and replay.
    """

    turn_number: int = Field(ge=1, description="Turn this event occurred")
    phase: GamePhase = Field(description="Phase this event occurred")
    event_type: str = Field(description="Type of event (e.g., 'movement', 'collision', 'firing')")

    # Core event data
    summary: str = Field(description="Human-readable summary of the event")

    # Optional dice information
    dice_roll: DiceRoll | None = Field(default=None, description="Dice roll if applicable")
    modifiers: dict[str, int] = Field(default_factory=dict, description="Modifiers applied to roll")

    # Optional state changes
    state_diff: dict[str, Any] = Field(
        default_factory=dict,
        description="State changes caused by this event (for debugging)",
    )

    # Additional context
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional event-specific data"
    )
