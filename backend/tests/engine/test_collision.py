"""Tests for collision detection and resolution."""

import pytest

from wsim_core.engine import (
    CollisionDetectionError,
    SeededRNG,
    detect_and_resolve_collisions,
    detect_collisions,
    detect_hex_occupancy,
    get_ship_hexes,
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
def ship_p1_at_10_10() -> Ship:
    """Create P1 ship at position (10,10) facing north."""
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
    )


@pytest.fixture
def ship_p2_at_12_10() -> Ship:
    """Create P2 ship at position (12,10) facing west."""
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
    )


# ============================================================================
# Hex Occupancy Tests
# ============================================================================


def test_get_ship_hexes(ship_p1_at_10_10: Ship):
    """Test getting hexes occupied by a ship."""
    hexes = get_ship_hexes(ship_p1_at_10_10)
    assert len(hexes) == 2
    assert HexCoord(col=10, row=10) in hexes  # bow
    assert HexCoord(col=10, row=11) in hexes  # stern


def test_detect_hex_occupancy_no_collision(ship_p1_at_10_10: Ship, ship_p2_at_12_10: Ship):
    """Test detecting hex occupancy when ships don't collide."""
    ships = {"p1_ship_1": ship_p1_at_10_10, "p2_ship_1": ship_p2_at_12_10}

    occupancy = detect_hex_occupancy(ships)

    # Each hex should have exactly one ship
    assert HexCoord(col=10, row=10) in occupancy
    assert len(occupancy[HexCoord(col=10, row=10)]) == 1
    assert occupancy[HexCoord(col=10, row=10)][0] == "p1_ship_1"

    assert HexCoord(col=12, row=10) in occupancy
    assert len(occupancy[HexCoord(col=12, row=10)]) == 1
    assert occupancy[HexCoord(col=12, row=10)][0] == "p2_ship_1"


def test_detect_hex_occupancy_with_collision(ship_p1_at_10_10: Ship):
    """Test detecting hex occupancy when two ships occupy same hex."""
    # Create second ship at same position
    ship_p2_same_pos = ship_p1_at_10_10.model_copy(deep=True)
    ship_p2_same_pos = ship_p2_same_pos.model_copy(update={"id": "p2_ship_1", "side": Side.P2})

    ships = {"p1_ship_1": ship_p1_at_10_10, "p2_ship_1": ship_p2_same_pos}

    occupancy = detect_hex_occupancy(ships)

    # Bow hex should have both ships
    assert HexCoord(col=10, row=10) in occupancy
    assert len(occupancy[HexCoord(col=10, row=10)]) == 2
    assert set(occupancy[HexCoord(col=10, row=10)]) == {"p1_ship_1", "p2_ship_1"}


# ============================================================================
# Collision Detection Tests
# ============================================================================


def test_detect_collisions_no_collision(ship_p1_at_10_10: Ship, ship_p2_at_12_10: Ship):
    """Test collision detection when ships don't collide."""
    ships_before = {"p1_ship_1": ship_p1_at_10_10, "p2_ship_1": ship_p2_at_12_10}
    ships_after = ships_before  # No movement

    collisions = detect_collisions(ships_before, ships_after)

    assert len(collisions) == 0


def test_detect_collisions_bow_collision(ship_p1_at_10_10: Ship, ship_p2_at_12_10: Ship):
    """Test detecting collision when two ships end up in same hex (bow collision)."""
    ships_before = {"p1_ship_1": ship_p1_at_10_10, "p2_ship_1": ship_p2_at_12_10}

    # Move P2 ship to collide with P1 ship's bow
    ship_p2_moved = ship_p2_at_12_10.model_copy(
        update={
            "bow_hex": HexCoord(col=10, row=10),  # Same as P1's bow
            "stern_hex": HexCoord(col=11, row=10),
        }
    )
    ships_after = {"p1_ship_1": ship_p1_at_10_10, "p2_ship_1": ship_p2_moved}

    collisions = detect_collisions(ships_before, ships_after)

    assert len(collisions) == 1
    collision_hex, ship_ids = collisions[0]
    assert collision_hex == HexCoord(col=10, row=10)
    assert set(ship_ids) == {"p1_ship_1", "p2_ship_1"}


def test_detect_collisions_stern_collision(ship_p1_at_10_10: Ship, ship_p2_at_12_10: Ship):
    """Test detecting collision when ship moves into another's stern."""
    ships_before = {"p1_ship_1": ship_p1_at_10_10, "p2_ship_1": ship_p2_at_12_10}

    # Move P2 ship to collide with P1 ship's stern
    ship_p2_moved = ship_p2_at_12_10.model_copy(
        update={
            "bow_hex": HexCoord(col=10, row=11),  # Same as P1's stern
            "stern_hex": HexCoord(col=11, row=11),
        }
    )
    ships_after = {"p1_ship_1": ship_p1_at_10_10, "p2_ship_1": ship_p2_moved}

    collisions = detect_collisions(ships_before, ships_after)

    assert len(collisions) == 1
    collision_hex, ship_ids = collisions[0]
    assert collision_hex == HexCoord(col=10, row=11)
    assert set(ship_ids) == {"p1_ship_1", "p2_ship_1"}


def test_detect_collisions_multiple_ships_same_hex():
    """Test detecting collision with three ships in same hex."""
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
    )

    ship2 = ship1.model_copy(deep=True, update={"id": "ship_2", "name": "Ship 2"})
    ship3 = ship1.model_copy(deep=True, update={"id": "ship_3", "name": "Ship 3"})

    ships_before = {"ship_1": ship1, "ship_2": ship2, "ship_3": ship3}
    ships_after = ships_before

    collisions = detect_collisions(ships_before, ships_after)

    assert len(collisions) >= 1  # At least one collision at bow hex
    # Find collision at bow hex
    bow_collision = next(c for c in collisions if c[0] == HexCoord(col=10, row=10))
    assert len(bow_collision[1]) == 3  # All three ships


# ============================================================================
# Collision Resolution Tests
# ============================================================================


def test_detect_and_resolve_collisions_no_collision(
    ship_p1_at_10_10: Ship, ship_p2_at_12_10: Ship, rng: SeededRNG
):
    """Test collision resolution when there are no collisions."""
    ships_before = {"p1_ship_1": ship_p1_at_10_10, "p2_ship_1": ship_p2_at_12_10}
    ships_after = ships_before

    resolved_ships, result = detect_and_resolve_collisions(
        ships_before=ships_before, ships_after=ships_after, rng=rng, turn_number=1
    )

    assert len(result.collisions) == 0
    assert len(result.events) == 0
    assert resolved_ships == ships_after


def test_detect_and_resolve_collisions_stationary_priority(
    ship_p1_at_10_10: Ship, ship_p2_at_12_10: Ship, rng: SeededRNG
):
    """Test collision resolution when one ship was stationary (should have priority)."""
    ships_before = {"p1_ship_1": ship_p1_at_10_10, "p2_ship_1": ship_p2_at_12_10}

    # P2 moves into P1's bow hex
    ship_p2_moved = ship_p2_at_12_10.model_copy(
        update={
            "bow_hex": HexCoord(col=10, row=10),  # Collision with P1's bow
            "stern_hex": HexCoord(col=11, row=10),
        }
    )
    ships_after = {"p1_ship_1": ship_p1_at_10_10, "p2_ship_1": ship_p2_moved}

    resolved_ships, result = detect_and_resolve_collisions(
        ships_before=ships_before, ships_after=ships_after, rng=rng, turn_number=1
    )

    # P1 was stationary, should occupy hex
    assert len(result.collisions) == 1
    collision = result.collisions[0]
    assert collision.occupying_ship_id == "p1_ship_1"
    assert "p2_ship_1" in collision.displaced_ship_ids

    # P2 should be moved back to previous position
    assert resolved_ships["p2_ship_1"].bow_hex == HexCoord(col=12, row=10)
    assert resolved_ships["p2_ship_1"].stern_hex == HexCoord(col=13, row=10)

    # P1 should remain in place
    assert resolved_ships["p1_ship_1"].bow_hex == HexCoord(col=10, row=10)

    # Should have event log entry
    assert len(result.events) == 1
    assert result.events[0].event_type == "collision"
    assert "stationary_priority" in result.events[0].metadata["resolution_method"]


def test_detect_and_resolve_collisions_both_moving(
    ship_p1_at_10_10: Ship, ship_p2_at_12_10: Ship, rng: SeededRNG
):
    """Test collision resolution when both ships move into same hex."""
    # Start with ships in different positions
    ship_p1_before = ship_p1_at_10_10.model_copy(
        update={"bow_hex": HexCoord(col=8, row=10), "stern_hex": HexCoord(col=8, row=11)}
    )
    ship_p2_before = ship_p2_at_12_10.model_copy(
        update={"bow_hex": HexCoord(col=14, row=10), "stern_hex": HexCoord(col=15, row=10)}
    )
    ships_before = {"p1_ship_1": ship_p1_before, "p2_ship_1": ship_p2_before}

    # Both move to same hex
    ship_p1_after = ship_p1_before.model_copy(
        update={"bow_hex": HexCoord(col=11, row=10), "stern_hex": HexCoord(col=11, row=11)}
    )
    ship_p2_after = ship_p2_before.model_copy(
        update={"bow_hex": HexCoord(col=11, row=10), "stern_hex": HexCoord(col=10, row=10)}
    )
    ships_after = {"p1_ship_1": ship_p1_after, "p2_ship_1": ship_p2_after}

    resolved_ships, result = detect_and_resolve_collisions(
        ships_before=ships_before, ships_after=ships_after, rng=rng, turn_number=1
    )

    # Should resolve collision
    assert len(result.collisions) == 1
    collision = result.collisions[0]

    # One ship should occupy, other displaced
    assert collision.occupying_ship_id in ["p1_ship_1", "p2_ship_1"]
    assert len(collision.displaced_ship_ids) == 1

    # Displaced ship should be back at previous position
    displaced_id = collision.displaced_ship_ids[0]
    if displaced_id == "p1_ship_1":
        assert resolved_ships["p1_ship_1"].bow_hex == HexCoord(col=8, row=10)
    else:
        assert resolved_ships["p2_ship_1"].bow_hex == HexCoord(col=14, row=10)

    # Event should indicate random selection
    assert len(result.events) == 1
    assert "random_selection" in result.events[0].metadata["resolution_method"]


def test_collision_resolution_truncates_movement():
    """Test that collision resolution marks movement as truncated."""
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
    )

    ship2 = ship1.model_copy(deep=True, update={"id": "ship_2", "name": "Ship 2", "side": Side.P2})

    ships_before = {"ship_1": ship1, "ship_2": ship2}
    ships_after = ships_before

    rng = SeededRNG(seed=123)
    resolved_ships, result = detect_and_resolve_collisions(
        ships_before=ships_before, ships_after=ships_after, rng=rng, turn_number=1
    )

    assert len(result.collisions) >= 1
    # All collision resolutions should truncate movement
    for collision in result.collisions:
        assert collision.truncate_movement is True


def test_collision_with_deterministic_rng():
    """Test that collision resolution is deterministic with seeded RNG."""
    ship1_before = Ship(
        id="ship_1",
        name="Ship 1",
        side=Side.P1,
        bow_hex=HexCoord(col=8, row=10),
        stern_hex=HexCoord(col=8, row=11),
        facing=Facing.E,
        battle_sail_speed=4,
        guns_L=10,
        guns_R=10,
        hull=12,
        rigging=10,
        crew=10,
        marines=2,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
    )

    ship2_before = Ship(
        id="ship_2",
        name="Ship 2",
        side=Side.P2,
        bow_hex=HexCoord(col=14, row=10),
        stern_hex=HexCoord(col=15, row=10),
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
    )

    ships_before = {"ship_1": ship1_before, "ship_2": ship2_before}

    # Both move to same hex
    ship1_after = ship1_before.model_copy(
        update={"bow_hex": HexCoord(col=11, row=10), "stern_hex": HexCoord(col=10, row=10)}
    )
    ship2_after = ship2_before.model_copy(
        update={"bow_hex": HexCoord(col=11, row=10), "stern_hex": HexCoord(col=12, row=10)}
    )
    ships_after = {"ship_1": ship1_after, "ship_2": ship2_after}

    # Run twice with same seed
    rng1 = SeededRNG(seed=999)
    result1_ships, result1 = detect_and_resolve_collisions(
        ships_before=ships_before, ships_after=ships_after, rng=rng1, turn_number=1
    )

    rng2 = SeededRNG(seed=999)
    result2_ships, result2 = detect_and_resolve_collisions(
        ships_before=ships_before, ships_after=ships_after, rng=rng2, turn_number=1
    )

    # Results should be identical
    assert result1.collisions[0].occupying_ship_id == result2.collisions[0].occupying_ship_id
    assert result1_ships["ship_1"].bow_hex == result2_ships["ship_1"].bow_hex
    assert result1_ships["ship_2"].bow_hex == result2_ships["ship_2"].bow_hex


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_collision_detection_error_on_invalid_input():
    """Test that collision resolution raises error with invalid input."""
    ship = Ship(
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
    )

    ships = {"ship_1": ship}
    rng = SeededRNG(seed=42)

    # Try to resolve collision with only one ship (should error)
    from wsim_core.engine.collision import resolve_collision

    with pytest.raises(CollisionDetectionError):
        resolve_collision(
            collision_hex=HexCoord(col=10, row=10),
            ship_ids=["ship_1"],  # Only one ship - invalid
            ships_before=ships,
            ships_after=ships,
            rng=rng,
            turn_number=1,
        )
