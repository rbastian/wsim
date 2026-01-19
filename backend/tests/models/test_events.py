"""Tests for event log models."""

import pytest
from pydantic import ValidationError

from wsim_core.models.common import GamePhase
from wsim_core.models.events import DiceRoll, EventLogEntry


def test_dice_roll_creation() -> None:
    """Test basic dice roll creation."""
    roll = DiceRoll(num_dice=2, die_type=6, rolls=[3, 5], total=8)

    assert roll.num_dice == 2
    assert roll.die_type == 6
    assert roll.rolls == [3, 5]
    assert roll.total == 8


def test_dice_roll_validation() -> None:
    """Test dice roll validation."""
    # Valid
    DiceRoll(num_dice=1, die_type=6, rolls=[4], total=4)

    # Invalid num_dice
    with pytest.raises(ValidationError):
        DiceRoll(num_dice=0, die_type=6, rolls=[], total=0)

    # Invalid die_type
    with pytest.raises(ValidationError):
        DiceRoll(num_dice=1, die_type=1, rolls=[1], total=1)


def test_event_log_entry_minimal() -> None:
    """Test event log entry with minimal fields."""
    event = EventLogEntry(
        turn_number=1,
        phase=GamePhase.MOVEMENT,
        event_type="movement",
        summary="Ship moved forward 2 hexes",
    )

    assert event.turn_number == 1
    assert event.phase == GamePhase.MOVEMENT
    assert event.event_type == "movement"
    assert event.summary == "Ship moved forward 2 hexes"
    assert event.dice_roll is None
    assert event.modifiers == {}
    assert event.state_diff == {}
    assert event.metadata == {}


def test_event_log_entry_with_dice() -> None:
    """Test event log entry with dice roll."""
    roll = DiceRoll(num_dice=1, die_type=6, rolls=[4], total=4)
    event = EventLogEntry(
        turn_number=2,
        phase=GamePhase.COMBAT,
        event_type="firing",
        summary="HMS Test fired at FS Vengeur",
        dice_roll=roll,
        modifiers={"range": -1, "crew": 0},
    )

    assert event.dice_roll == roll
    assert event.modifiers == {"range": -1, "crew": 0}


def test_event_log_entry_with_state_diff() -> None:
    """Test event log entry with state changes."""
    event = EventLogEntry(
        turn_number=2,
        phase=GamePhase.COMBAT,
        event_type="damage",
        summary="FS Vengeur took 2 hull damage",
        state_diff={"ship_id": "p2_ship_1", "hull_before": 12, "hull_after": 10},
    )

    assert event.state_diff["ship_id"] == "p2_ship_1"
    assert event.state_diff["hull_before"] == 12
    assert event.state_diff["hull_after"] == 10


def test_event_log_entry_with_metadata() -> None:
    """Test event log entry with metadata."""
    event = EventLogEntry(
        turn_number=1,
        phase=GamePhase.MOVEMENT,
        event_type="collision",
        summary="HMS Test collided with FS Vengeur",
        metadata={"ship_1": "p1_ship_1", "ship_2": "p2_ship_1", "hex": "5,10"},
    )

    assert event.metadata["ship_1"] == "p1_ship_1"
    assert event.metadata["ship_2"] == "p2_ship_1"
    assert event.metadata["hex"] == "5,10"


def test_event_log_entry_validation_turn_number() -> None:
    """Test event log entry requires positive turn number."""
    with pytest.raises(ValidationError):
        EventLogEntry(
            turn_number=0,  # Invalid
            phase=GamePhase.PLANNING,
            event_type="test",
            summary="Test event",
        )
