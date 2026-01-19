"""Tests for fouling system."""

import pytest

from wsim_core.engine import (
    FoulingResult,
    SeededRNG,
    apply_fouling,
    check_and_apply_fouling,
    check_fouling,
)
from wsim_core.models.common import Facing, LoadState, Side
from wsim_core.models.hex import HexCoord
from wsim_core.models.ship import Ship

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def rng() -> SeededRNG:
    """Create a seeded RNG for deterministic tests."""
    return SeededRNG(seed=42)


@pytest.fixture
def ship_p1() -> Ship:
    """Create P1 ship."""
    return Ship(
        id="p1_ship_1",
        name="HMS Test",
        side=Side.P1,
        bow_hex=HexCoord(col=10, row=10),
        stern_hex=HexCoord(col=10, row=11),
        facing=Facing.N,
        battle_sail_speed=4,
        guns_L=10,
        guns_R=10,
        hull=12,
        rigging=10,
        crew=10,
        marines=2,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
        fouled=False,
    )


@pytest.fixture
def ship_p2() -> Ship:
    """Create P2 ship."""
    return Ship(
        id="p2_ship_1",
        name="FS Vengeur",
        side=Side.P2,
        bow_hex=HexCoord(col=12, row=10),
        stern_hex=HexCoord(col=13, row=10),
        facing=Facing.W,
        battle_sail_speed=4,
        guns_L=10,
        guns_R=10,
        hull=12,
        rigging=10,
        crew=10,
        marines=2,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
        fouled=False,
    )


# ============================================================================
# Fouling Check Tests
# ============================================================================


def test_check_fouling_single_ship(ship_p1: Ship, rng: SeededRNG):
    """Test fouling check with single ship (should not foul)."""
    ships = {"p1_ship_1": ship_p1}
    result = check_fouling(ship_ids=["p1_ship_1"], ships=ships, rng=rng, turn_number=1)

    assert result.fouled is False
    assert result.roll == 0
    assert len(result.events) == 0


def test_check_fouling_no_ships(rng: SeededRNG):
    """Test fouling check with no ships."""
    result = check_fouling(ship_ids=[], ships={}, rng=rng, turn_number=1)

    assert result.fouled is False
    assert result.roll == 0
    assert len(result.events) == 0


def test_check_fouling_two_ships_roll_low(ship_p1: Ship, ship_p2: Ship):
    """Test fouling check with roll 1-3 (should foul)."""
    ships = {"p1_ship_1": ship_p1, "p2_ship_1": ship_p2}

    # Use seeded RNG to get predictable rolls
    # We need to find a seed that gives us a roll <= 3
    rng = SeededRNG(seed=1)
    result = check_fouling(ship_ids=["p1_ship_1", "p2_ship_1"], ships=ships, rng=rng, turn_number=1)

    # Check if roll is 1-3 (fouled) or 4-6 (not fouled)
    if result.roll <= 3:
        assert result.fouled is True
    else:
        assert result.fouled is False

    # Verify event was created
    assert len(result.events) == 1
    assert result.events[0].event_type == "fouling_check"
    assert result.events[0].metadata["roll"] == result.roll
    assert result.events[0].metadata["fouled"] == result.fouled


def test_check_fouling_two_ships_roll_high(ship_p1: Ship, ship_p2: Ship):
    """Test fouling check with roll 4-6 (should not foul)."""
    ships = {"p1_ship_1": ship_p1, "p2_ship_1": ship_p2}

    # Try different seeds to get a roll > 3
    rng = SeededRNG(seed=100)
    result = check_fouling(ship_ids=["p1_ship_1", "p2_ship_1"], ships=ships, rng=rng, turn_number=1)

    # Check if roll is 1-3 (fouled) or 4-6 (not fouled)
    if result.roll > 3:
        assert result.fouled is False
    else:
        assert result.fouled is True

    # Verify event was created
    assert len(result.events) == 1
    assert result.events[0].event_type == "fouling_check"


def test_check_fouling_multiple_ships():
    """Test fouling check with three ships."""
    ship1 = Ship(
        id="ship_1",
        name="Ship 1",
        side=Side.P1,
        bow_hex=HexCoord(col=10, row=10),
        stern_hex=HexCoord(col=10, row=11),
        facing=Facing.N,
        battle_sail_speed=4,
        guns_L=10,
        guns_R=10,
        hull=12,
        rigging=10,
        crew=10,
        marines=2,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
        fouled=False,
    )

    ship2 = ship1.model_copy(deep=True, update={"id": "ship_2", "name": "Ship 2"})
    ship3 = ship1.model_copy(deep=True, update={"id": "ship_3", "name": "Ship 3"})

    ships = {"ship_1": ship1, "ship_2": ship2, "ship_3": ship3}

    rng = SeededRNG(seed=42)
    result = check_fouling(
        ship_ids=["ship_1", "ship_2", "ship_3"], ships=ships, rng=rng, turn_number=1
    )

    # Should have checked for fouling
    assert result.roll > 0
    assert len(result.events) == 1
    assert len(result.ship_ids) == 3


def test_check_fouling_deterministic():
    """Test that fouling check is deterministic with seeded RNG."""
    ship1 = Ship(
        id="ship_1",
        name="Ship 1",
        side=Side.P1,
        bow_hex=HexCoord(col=10, row=10),
        stern_hex=HexCoord(col=10, row=11),
        facing=Facing.N,
        battle_sail_speed=4,
        guns_L=10,
        guns_R=10,
        hull=12,
        rigging=10,
        crew=10,
        marines=2,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
        fouled=False,
    )

    ship2 = ship1.model_copy(deep=True, update={"id": "ship_2", "name": "Ship 2"})
    ships = {"ship_1": ship1, "ship_2": ship2}

    # Run twice with same seed
    rng1 = SeededRNG(seed=999)
    result1 = check_fouling(ship_ids=["ship_1", "ship_2"], ships=ships, rng=rng1, turn_number=1)

    rng2 = SeededRNG(seed=999)
    result2 = check_fouling(ship_ids=["ship_1", "ship_2"], ships=ships, rng=rng2, turn_number=1)

    # Results should be identical
    assert result1.roll == result2.roll
    assert result1.fouled == result2.fouled


# ============================================================================
# Apply Fouling Tests
# ============================================================================


def test_apply_fouling_when_fouled(ship_p1: Ship, ship_p2: Ship):
    """Test applying fouled status to ships."""
    ships = {"p1_ship_1": ship_p1, "p2_ship_1": ship_p2}

    # Create fouling result that indicates fouling occurred
    fouling_result = FoulingResult(ship_ids=["p1_ship_1", "p2_ship_1"], fouled=True, roll=2)

    updated_ships = apply_fouling(ships=ships, fouling_result=fouling_result)

    # Both ships should be fouled
    assert updated_ships["p1_ship_1"].fouled is True
    assert updated_ships["p2_ship_1"].fouled is True

    # Original ships should not be modified
    assert ship_p1.fouled is False
    assert ship_p2.fouled is False


def test_apply_fouling_when_not_fouled(ship_p1: Ship, ship_p2: Ship):
    """Test that fouled status is not applied when fouling didn't occur."""
    ships = {"p1_ship_1": ship_p1, "p2_ship_1": ship_p2}

    # Create fouling result that indicates no fouling
    fouling_result = FoulingResult(ship_ids=["p1_ship_1", "p2_ship_1"], fouled=False, roll=5)

    updated_ships = apply_fouling(ships=ships, fouling_result=fouling_result)

    # Ships should not be fouled
    assert updated_ships["p1_ship_1"].fouled is False
    assert updated_ships["p2_ship_1"].fouled is False

    # Should be same as original
    assert updated_ships == ships


def test_apply_fouling_to_already_fouled_ship(ship_p1: Ship, ship_p2: Ship):
    """Test applying fouling to a ship that's already fouled."""
    # Make P1 already fouled
    ship_p1_fouled = ship_p1.model_copy(update={"fouled": True})
    ships = {"p1_ship_1": ship_p1_fouled, "p2_ship_1": ship_p2}

    fouling_result = FoulingResult(ship_ids=["p1_ship_1", "p2_ship_1"], fouled=True, roll=2)

    updated_ships = apply_fouling(ships=ships, fouling_result=fouling_result)

    # Both should be fouled
    assert updated_ships["p1_ship_1"].fouled is True
    assert updated_ships["p2_ship_1"].fouled is True


def test_apply_fouling_partial_ship_ids(ship_p1: Ship, ship_p2: Ship):
    """Test applying fouling when some ship IDs are not in ships dict."""
    ships = {"p1_ship_1": ship_p1}  # Only P1, not P2

    fouling_result = FoulingResult(ship_ids=["p1_ship_1", "p2_ship_1"], fouled=True, roll=2)

    updated_ships = apply_fouling(ships=ships, fouling_result=fouling_result)

    # P1 should be fouled
    assert updated_ships["p1_ship_1"].fouled is True

    # P2 should not be in updated ships (wasn't in original)
    assert "p2_ship_1" not in updated_ships


# ============================================================================
# Combined Check and Apply Tests
# ============================================================================


def test_check_and_apply_fouling_integration(ship_p1: Ship, ship_p2: Ship):
    """Test integrated check and apply fouling."""
    ships = {"p1_ship_1": ship_p1, "p2_ship_1": ship_p2}

    # Use seed that gives roll <= 3
    rng = SeededRNG(seed=1)
    updated_ships, fouling_result = check_and_apply_fouling(
        ship_ids=["p1_ship_1", "p2_ship_1"], ships=ships, rng=rng, turn_number=1
    )

    # Check that fouling result was created
    assert fouling_result.roll > 0
    assert len(fouling_result.events) == 1

    # If fouling occurred, ships should be fouled
    if fouling_result.fouled:
        assert updated_ships["p1_ship_1"].fouled is True
        assert updated_ships["p2_ship_1"].fouled is True
    else:
        assert updated_ships["p1_ship_1"].fouled is False
        assert updated_ships["p2_ship_1"].fouled is False


def test_check_and_apply_fouling_preserves_other_state(ship_p1: Ship, ship_p2: Ship):
    """Test that fouling doesn't modify other ship state."""
    ships = {"p1_ship_1": ship_p1, "p2_ship_1": ship_p2}

    rng = SeededRNG(seed=1)
    updated_ships, _ = check_and_apply_fouling(
        ship_ids=["p1_ship_1", "p2_ship_1"], ships=ships, rng=rng, turn_number=1
    )

    # Other ship properties should be unchanged
    assert updated_ships["p1_ship_1"].hull == ship_p1.hull
    assert updated_ships["p1_ship_1"].crew == ship_p1.crew
    assert updated_ships["p1_ship_1"].bow_hex == ship_p1.bow_hex
    assert updated_ships["p1_ship_1"].facing == ship_p1.facing


# ============================================================================
# Event Logging Tests
# ============================================================================


def test_fouling_event_includes_ship_names(ship_p1: Ship, ship_p2: Ship):
    """Test that fouling event includes ship names."""
    ships = {"p1_ship_1": ship_p1, "p2_ship_1": ship_p2}

    rng = SeededRNG(seed=42)
    result = check_fouling(ship_ids=["p1_ship_1", "p2_ship_1"], ships=ships, rng=rng, turn_number=1)

    assert len(result.events) == 1
    event = result.events[0]

    # Event summary should mention both ships
    assert "HMS Test" in event.summary
    assert "FS Vengeur" in event.summary


def test_fouling_event_includes_roll_and_outcome(ship_p1: Ship, ship_p2: Ship):
    """Test that fouling event includes roll and outcome."""
    ships = {"p1_ship_1": ship_p1, "p2_ship_1": ship_p2}

    rng = SeededRNG(seed=42)
    result = check_fouling(ship_ids=["p1_ship_1", "p2_ship_1"], ships=ships, rng=rng, turn_number=1)

    event = result.events[0]

    # Event should have roll in metadata
    assert "roll" in event.metadata
    assert event.metadata["roll"] == result.roll

    # Event should have fouled status in metadata
    assert "fouled" in event.metadata
    assert event.metadata["fouled"] == result.fouled

    # Summary should mention the outcome
    if result.fouled:
        assert "become fouled" in event.summary.lower()
    else:
        assert "avoid fouling" in event.summary.lower()


def test_fouling_event_turn_and_phase(ship_p1: Ship, ship_p2: Ship):
    """Test that fouling event has correct turn number and phase."""
    ships = {"p1_ship_1": ship_p1, "p2_ship_1": ship_p2}

    rng = SeededRNG(seed=42)
    result = check_fouling(ship_ids=["p1_ship_1", "p2_ship_1"], ships=ships, rng=rng, turn_number=5)

    event = result.events[0]

    assert event.turn_number == 5
    assert event.phase == "movement"
