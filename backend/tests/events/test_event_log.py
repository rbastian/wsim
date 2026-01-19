"""Tests for EventLog class."""

from wsim_core.events import EventLog
from wsim_core.models.common import GamePhase
from wsim_core.models.events import DiceRoll, EventLogEntry


def create_test_event(
    turn: int = 1,
    phase: GamePhase = GamePhase.MOVEMENT,
    event_type: str = "test",
    summary: str = "Test event",
) -> EventLogEntry:
    """Create a test event entry."""
    return EventLogEntry(turn_number=turn, phase=phase, event_type=event_type, summary=summary)


def test_event_log_creation():
    """Test creating an empty event log."""
    log = EventLog()
    assert log.event_count() == 0
    assert log.get_all_events() == []


def test_add_single_event():
    """Test adding a single event."""
    log = EventLog()
    event = create_test_event()

    log.add_event(event)

    assert log.event_count() == 1
    assert log.get_all_events() == [event]


def test_add_multiple_events():
    """Test adding multiple events one at a time."""
    log = EventLog()
    event1 = create_test_event(turn=1, summary="Event 1")
    event2 = create_test_event(turn=1, summary="Event 2")

    log.add_event(event1)
    log.add_event(event2)

    assert log.event_count() == 2
    events = log.get_all_events()
    assert events == [event1, event2]


def test_add_events_batch():
    """Test adding multiple events in a batch."""
    log = EventLog()
    events = [
        create_test_event(turn=1, summary="Event 1"),
        create_test_event(turn=1, summary="Event 2"),
        create_test_event(turn=1, summary="Event 3"),
    ]

    log.add_events(events)

    assert log.event_count() == 3
    assert log.get_all_events() == events


def test_get_all_events_returns_copy():
    """Test that get_all_events returns a copy, not the original list."""
    log = EventLog()
    event = create_test_event()
    log.add_event(event)

    events = log.get_all_events()
    events.append(create_test_event(turn=2))

    # Original log should be unchanged
    assert log.event_count() == 1


def test_get_events_for_turn():
    """Test filtering events by turn number."""
    log = EventLog()
    turn1_events = [
        create_test_event(turn=1, summary="Turn 1 Event 1"),
        create_test_event(turn=1, summary="Turn 1 Event 2"),
    ]
    turn2_events = [
        create_test_event(turn=2, summary="Turn 2 Event 1"),
    ]

    log.add_events(turn1_events + turn2_events)

    assert log.get_events_for_turn(1) == turn1_events
    assert log.get_events_for_turn(2) == turn2_events
    assert log.get_events_for_turn(3) == []


def test_get_events_for_phase():
    """Test filtering events by turn and phase."""
    log = EventLog()
    movement_events = [
        create_test_event(turn=1, phase=GamePhase.MOVEMENT, summary="Move 1"),
        create_test_event(turn=1, phase=GamePhase.MOVEMENT, summary="Move 2"),
    ]
    combat_events = [
        create_test_event(turn=1, phase=GamePhase.COMBAT, summary="Fire 1"),
    ]

    log.add_events(movement_events + combat_events)

    assert log.get_events_for_phase(1, GamePhase.MOVEMENT) == movement_events
    assert log.get_events_for_phase(1, GamePhase.COMBAT) == combat_events
    assert log.get_events_for_phase(1, GamePhase.RELOAD) == []
    assert log.get_events_for_phase(2, GamePhase.MOVEMENT) == []


def test_get_events_by_type():
    """Test filtering events by event type."""
    log = EventLog()
    collision_events = [
        create_test_event(event_type="collision", summary="Collision 1"),
        create_test_event(event_type="collision", summary="Collision 2"),
    ]
    firing_events = [
        create_test_event(event_type="firing", summary="Fire 1"),
    ]

    log.add_events(collision_events + firing_events)

    assert log.get_events_by_type("collision") == collision_events
    assert log.get_events_by_type("firing") == firing_events
    assert log.get_events_by_type("damage") == []


def test_get_recent_events():
    """Test getting most recent N events."""
    log = EventLog()
    events = [
        create_test_event(turn=1, summary="Event 1"),
        create_test_event(turn=1, summary="Event 2"),
        create_test_event(turn=2, summary="Event 3"),
        create_test_event(turn=2, summary="Event 4"),
        create_test_event(turn=2, summary="Event 5"),
    ]
    log.add_events(events)

    recent_2 = log.get_recent_events(2)
    assert len(recent_2) == 2
    assert recent_2 == events[-2:]

    recent_all = log.get_recent_events(10)
    assert recent_all == events

    recent_none = log.get_recent_events(0)
    assert recent_none == []


def test_clear():
    """Test clearing all events."""
    log = EventLog()
    log.add_events(
        [
            create_test_event(turn=1),
            create_test_event(turn=2),
        ]
    )

    assert log.event_count() == 2

    log.clear()

    assert log.event_count() == 0
    assert log.get_all_events() == []


def test_event_count():
    """Test event count tracking."""
    log = EventLog()
    assert log.event_count() == 0

    log.add_event(create_test_event())
    assert log.event_count() == 1

    log.add_events([create_test_event(), create_test_event()])
    assert log.event_count() == 3

    log.clear()
    assert log.event_count() == 0


def test_get_turn_summary():
    """Test getting event count summary by phase."""
    log = EventLog()
    log.add_events(
        [
            create_test_event(turn=1, phase=GamePhase.MOVEMENT),
            create_test_event(turn=1, phase=GamePhase.MOVEMENT),
            create_test_event(turn=1, phase=GamePhase.COMBAT),
            create_test_event(turn=2, phase=GamePhase.COMBAT),
        ]
    )

    summary_turn1 = log.get_turn_summary(1)
    assert summary_turn1[GamePhase.MOVEMENT] == 2
    assert summary_turn1[GamePhase.COMBAT] == 1
    assert GamePhase.RELOAD not in summary_turn1

    summary_turn2 = log.get_turn_summary(2)
    assert summary_turn2[GamePhase.COMBAT] == 1
    assert GamePhase.MOVEMENT not in summary_turn2


def test_has_events_for_turn():
    """Test checking if events exist for a turn."""
    log = EventLog()
    log.add_events(
        [
            create_test_event(turn=1),
            create_test_event(turn=1),
            create_test_event(turn=3),
        ]
    )

    assert log.has_events_for_turn(1) is True
    assert log.has_events_for_turn(2) is False
    assert log.has_events_for_turn(3) is True


def test_event_with_dice_roll():
    """Test adding events with dice roll information."""
    log = EventLog()
    dice_roll = DiceRoll(num_dice=2, die_type=6, rolls=[3, 5], total=8)
    event = EventLogEntry(
        turn_number=1,
        phase=GamePhase.COMBAT,
        event_type="firing",
        summary="Ship fired broadside",
        dice_roll=dice_roll,
        modifiers={"crew_quality": -1, "range": -1},
    )

    log.add_event(event)

    retrieved = log.get_all_events()[0]
    assert retrieved.dice_roll is not None
    assert retrieved.dice_roll.total == 8
    assert retrieved.modifiers == {"crew_quality": -1, "range": -1}


def test_event_with_state_diff():
    """Test adding events with state diff information."""
    log = EventLog()
    event = EventLogEntry(
        turn_number=1,
        phase=GamePhase.MOVEMENT,
        event_type="collision",
        summary="Ships collided",
        state_diff={"ship_a_position": {"before": [5, 10], "after": [4, 10]}},
    )

    log.add_event(event)

    retrieved = log.get_all_events()[0]
    assert retrieved.state_diff is not None
    assert "ship_a_position" in retrieved.state_diff


def test_event_with_metadata():
    """Test adding events with custom metadata."""
    log = EventLog()
    event = EventLogEntry(
        turn_number=1,
        phase=GamePhase.COMBAT,
        event_type="damage",
        summary="Hull damaged",
        metadata={
            "ship_id": "ship_1",
            "damage_type": "hull",
            "damage_amount": 3,
        },
    )

    log.add_event(event)

    retrieved = log.get_all_events()[0]
    assert retrieved.metadata["ship_id"] == "ship_1"
    assert retrieved.metadata["damage_amount"] == 3


def test_chronological_ordering():
    """Test that events maintain chronological order."""
    log = EventLog()
    events = [
        create_test_event(turn=1, phase=GamePhase.PLANNING, summary="Planning"),
        create_test_event(turn=1, phase=GamePhase.MOVEMENT, summary="Movement"),
        create_test_event(turn=1, phase=GamePhase.COMBAT, summary="Combat"),
        create_test_event(turn=2, phase=GamePhase.PLANNING, summary="Planning T2"),
    ]

    log.add_events(events)

    retrieved = log.get_all_events()
    assert [e.summary for e in retrieved] == [
        "Planning",
        "Movement",
        "Combat",
        "Planning T2",
    ]


def test_multiple_batch_additions():
    """Test adding multiple batches of events."""
    log = EventLog()

    batch1 = [create_test_event(turn=1, summary=f"B1-{i}") for i in range(3)]
    batch2 = [create_test_event(turn=2, summary=f"B2-{i}") for i in range(2)]

    log.add_events(batch1)
    log.add_events(batch2)

    assert log.event_count() == 5
    assert len(log.get_events_for_turn(1)) == 3
    assert len(log.get_events_for_turn(2)) == 2


def test_empty_log_queries():
    """Test querying empty log returns appropriate empty results."""
    log = EventLog()

    assert log.get_all_events() == []
    assert log.get_events_for_turn(1) == []
    assert log.get_events_for_phase(1, GamePhase.MOVEMENT) == []
    assert log.get_events_by_type("test") == []
    assert log.get_recent_events(5) == []
    assert log.get_turn_summary(1) == {}
    assert log.has_events_for_turn(1) is False
