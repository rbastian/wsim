"""Tests for drift system."""

from wsim_core.engine.drift import (
    apply_drift,
    check_and_apply_drift,
    get_downwind_direction,
    update_drift_tracking,
)
from wsim_core.models.common import Facing, LoadState, Side, WindDirection
from wsim_core.models.hex import HexCoord
from wsim_core.models.ship import Ship


def create_test_ship(
    ship_id: str = "test_ship_1",
    name: str = "Test Ship",
    bow: tuple[int, int] = (10, 10),
    facing: Facing = Facing.N,
    turns_without_bow_advance: int = 0,
) -> Ship:
    """Create a test ship with default values."""
    return Ship(
        id=ship_id,
        name=name,
        side=Side.P1,
        bow_hex=HexCoord(col=bow[0], row=bow[1]),
        stern_hex=HexCoord(col=bow[0], row=bow[1] + 1),  # Simplified stern calc
        facing=facing,
        battle_sail_speed=4,
        guns_L=10,
        guns_R=10,
        hull=12,
        rigging=10,
        crew=10,
        marines=2,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
        turns_without_bow_advance=turns_without_bow_advance,
    )


# Test downwind direction calculation


def test_get_downwind_direction_north():
    """Wind from North blows South."""
    assert get_downwind_direction(WindDirection.N) == WindDirection.S


def test_get_downwind_direction_south():
    """Wind from South blows North."""
    assert get_downwind_direction(WindDirection.S) == WindDirection.N


def test_get_downwind_direction_east():
    """Wind from East blows West."""
    assert get_downwind_direction(WindDirection.E) == WindDirection.W


def test_get_downwind_direction_west():
    """Wind from West blows East."""
    assert get_downwind_direction(WindDirection.W) == WindDirection.E


def test_get_downwind_direction_all_compass_points():
    """Verify all 8 compass directions map correctly."""
    expected = {
        WindDirection.N: WindDirection.S,
        WindDirection.NE: WindDirection.SW,
        WindDirection.E: WindDirection.W,
        WindDirection.SE: WindDirection.NW,
        WindDirection.S: WindDirection.N,
        WindDirection.SW: WindDirection.NE,
        WindDirection.W: WindDirection.E,
        WindDirection.NW: WindDirection.SE,
    }

    for wind, expected_downwind in expected.items():
        assert get_downwind_direction(wind) == expected_downwind


# Test drift tracking updates


def test_update_drift_tracking_no_advance_increments():
    """Ship that doesn't advance bow increments counter."""
    ship = create_test_ship(turns_without_bow_advance=0)
    ships = {"ship1": ship}
    movement_result = {"ship1": False}  # Did not advance

    updated_ships = update_drift_tracking(ships, movement_result)

    assert updated_ships["ship1"].turns_without_bow_advance == 1


def test_update_drift_tracking_advance_resets():
    """Ship that advances bow resets counter to 0."""
    ship = create_test_ship(turns_without_bow_advance=2)
    ships = {"ship1": ship}
    movement_result = {"ship1": True}  # Advanced

    updated_ships = update_drift_tracking(ships, movement_result)

    assert updated_ships["ship1"].turns_without_bow_advance == 0


def test_update_drift_tracking_increments_from_previous():
    """Counter increments from previous value."""
    ship = create_test_ship(turns_without_bow_advance=1)
    ships = {"ship1": ship}
    movement_result = {"ship1": False}

    updated_ships = update_drift_tracking(ships, movement_result)

    assert updated_ships["ship1"].turns_without_bow_advance == 2


def test_update_drift_tracking_multiple_ships():
    """Track drift for multiple ships independently."""
    ship1 = create_test_ship(ship_id="ship1", turns_without_bow_advance=0)
    ship2 = create_test_ship(ship_id="ship2", turns_without_bow_advance=1)
    ships = {"ship1": ship1, "ship2": ship2}
    movement_result = {"ship1": True, "ship2": False}  # ship1 advances, ship2 doesn't

    updated_ships = update_drift_tracking(ships, movement_result)

    assert updated_ships["ship1"].turns_without_bow_advance == 0
    assert updated_ships["ship2"].turns_without_bow_advance == 2


def test_update_drift_tracking_missing_ship_treats_as_no_advance():
    """Ship not in movement_result is treated as no advance."""
    ship = create_test_ship(turns_without_bow_advance=0)
    ships = {"ship1": ship}
    movement_result = {}  # Empty

    updated_ships = update_drift_tracking(ships, movement_result)

    assert updated_ships["ship1"].turns_without_bow_advance == 1


# Test drift application


def test_apply_drift_no_drift_needed():
    """Ships with counter < 2 don't drift."""
    ship = create_test_ship(turns_without_bow_advance=1)
    ships = {"ship1": ship}

    updated_ships, result = apply_drift(ships, WindDirection.N, 25, 20, 1)

    assert updated_ships["ship1"].bow_hex == ship.bow_hex
    assert updated_ships["ship1"].stern_hex == ship.stern_hex
    assert len(result.drifted_ships) == 0
    assert len(result.events) == 0


def test_apply_drift_triggers_at_two_turns():
    """Ship drifts when counter >= 2."""
    ship = create_test_ship(bow=(10, 10), facing=Facing.N, turns_without_bow_advance=2)
    ships = {"ship1": ship}

    updated_ships, result = apply_drift(ships, WindDirection.N, 25, 20, 1)

    # Wind from N blows S, so ship drifts south
    assert updated_ships["ship1"].bow_hex.row > ship.bow_hex.row
    assert len(result.drifted_ships) == 1
    assert "ship1" in result.drifted_ships
    assert len(result.events) == 1
    assert result.events[0].event_type == "drift"


def test_apply_drift_resets_counter():
    """Drift resets turns_without_bow_advance to 0."""
    ship = create_test_ship(turns_without_bow_advance=3)
    ships = {"ship1": ship}

    updated_ships, result = apply_drift(ships, WindDirection.N, 25, 20, 1)

    assert updated_ships["ship1"].turns_without_bow_advance == 0


def test_apply_drift_moves_bow_and_stern():
    """Both bow and stern move when drifting."""
    ship = create_test_ship(bow=(10, 10), facing=Facing.E, turns_without_bow_advance=2)
    # Manually set stern for this test
    ship = ship.model_copy(update={"stern_hex": HexCoord(col=9, row=10)})
    original_bow = ship.bow_hex
    original_stern = ship.stern_hex
    ships = {"ship1": ship}

    updated_ships, result = apply_drift(ships, WindDirection.E, 25, 20, 1)

    # Wind from E blows W
    new_bow = updated_ships["ship1"].bow_hex
    new_stern = updated_ships["ship1"].stern_hex

    # Both should have moved west (col decreased)
    assert new_bow.col < original_bow.col
    assert new_stern.col < original_stern.col
    # Rows should be same (moving purely west in this case depends on col parity)
    # The exact row behavior depends on hex geometry


def test_apply_drift_wind_from_south():
    """Drift north when wind from south."""
    ship = create_test_ship(bow=(10, 10), facing=Facing.N, turns_without_bow_advance=2)
    ships = {"ship1": ship}

    updated_ships, result = apply_drift(ships, WindDirection.S, 25, 20, 1)

    # Wind from S blows N, so ship drifts north
    assert updated_ships["ship1"].bow_hex.row < ship.bow_hex.row


def test_apply_drift_out_of_bounds_north():
    """Ship at north edge doesn't drift north if would go out of bounds."""
    ship = create_test_ship(bow=(10, 0), facing=Facing.N, turns_without_bow_advance=2)
    ship = ship.model_copy(update={"stern_hex": HexCoord(col=10, row=1)})
    ships = {"ship1": ship}

    updated_ships, result = apply_drift(ships, WindDirection.S, 25, 20, 1)

    # Should not drift (would go out of bounds)
    assert updated_ships["ship1"].bow_hex == ship.bow_hex
    assert len(result.drifted_ships) == 0
    assert len(result.events) == 1
    assert result.events[0].event_type == "drift_blocked"


def test_apply_drift_out_of_bounds_south():
    """Ship at south edge doesn't drift south if would go out of bounds."""
    ship = create_test_ship(bow=(10, 19), facing=Facing.N, turns_without_bow_advance=2)
    ship = ship.model_copy(update={"stern_hex": HexCoord(col=10, row=18)})
    ships = {"ship1": ship}

    updated_ships, result = apply_drift(ships, WindDirection.N, 25, 20, 1)

    # Should not drift (would go out of bounds)
    assert updated_ships["ship1"].bow_hex == ship.bow_hex
    assert len(result.drifted_ships) == 0
    assert len(result.events) == 1
    assert result.events[0].event_type == "drift_blocked"


def test_apply_drift_multiple_ships():
    """Multiple ships can drift simultaneously."""
    ship1 = create_test_ship(ship_id="ship1", bow=(10, 10), turns_without_bow_advance=2)
    ship2 = create_test_ship(ship_id="ship2", bow=(15, 10), turns_without_bow_advance=3)
    ship3 = create_test_ship(ship_id="ship3", bow=(12, 10), turns_without_bow_advance=1)
    ships = {"ship1": ship1, "ship2": ship2, "ship3": ship3}

    updated_ships, result = apply_drift(ships, WindDirection.N, 25, 20, 1)

    # ship1 and ship2 should drift, ship3 should not
    assert len(result.drifted_ships) == 2
    assert "ship1" in result.drifted_ships
    assert "ship2" in result.drifted_ships
    assert "ship3" not in result.drifted_ships
    assert len(result.events) == 2


def test_apply_drift_event_includes_metadata():
    """Drift event includes full metadata."""
    ship = create_test_ship(
        ship_id="ship1", name="HMS Test", bow=(10, 10), turns_without_bow_advance=2
    )
    ships = {"ship1": ship}

    updated_ships, result = apply_drift(ships, WindDirection.N, 25, 20, 5)

    event = result.events[0]
    assert event.turn_number == 5
    assert event.phase == "movement"
    assert event.event_type == "drift"
    assert "ship1" in event.metadata["ship_id"]
    assert "HMS Test" in event.metadata["ship_name"]
    assert event.metadata["wind_direction"] == "N"
    assert event.metadata["drift_direction"] == "S"
    assert event.metadata["turns_without_advance"] == 2


# Test combined check_and_apply_drift function


def test_check_and_apply_drift_integration():
    """Full integration: update tracking and apply drift."""
    ship = create_test_ship(turns_without_bow_advance=1)
    ships = {"ship1": ship}
    movement_result = {"ship1": False}  # No advance

    # After this call, counter should be 2 and drift should apply
    updated_ships, result = check_and_apply_drift(
        ships, movement_result, WindDirection.N, 25, 20, 1
    )

    # Ship should have drifted (counter went 1->2 and triggered drift)
    assert len(result.drifted_ships) == 1
    assert updated_ships["ship1"].turns_without_bow_advance == 0  # Reset after drift
    assert len(result.events) == 1


def test_check_and_apply_drift_no_drift_after_reset():
    """Ship that advances doesn't drift even if counter was high."""
    ship = create_test_ship(turns_without_bow_advance=2)
    ships = {"ship1": ship}
    movement_result = {"ship1": True}  # Advanced

    updated_ships, result = check_and_apply_drift(
        ships, movement_result, WindDirection.N, 25, 20, 1
    )

    # Counter resets, no drift
    assert updated_ships["ship1"].turns_without_bow_advance == 0
    assert len(result.drifted_ships) == 0
    assert len(result.events) == 0


def test_check_and_apply_drift_sequence():
    """Simulate multiple turns of drift tracking."""
    ship = create_test_ship(turns_without_bow_advance=0)
    ships = {"ship1": ship}

    # Turn 1: no advance
    ships, result = check_and_apply_drift(ships, {"ship1": False}, WindDirection.N, 25, 20, 1)
    assert ships["ship1"].turns_without_bow_advance == 1
    assert len(result.drifted_ships) == 0

    # Turn 2: no advance (should drift now)
    ships, result = check_and_apply_drift(ships, {"ship1": False}, WindDirection.N, 25, 20, 2)
    assert ships["ship1"].turns_without_bow_advance == 0  # Reset
    assert len(result.drifted_ships) == 1

    # Turn 3: no advance again (counter at 1)
    ships, result = check_and_apply_drift(ships, {"ship1": False}, WindDirection.N, 25, 20, 3)
    assert ships["ship1"].turns_without_bow_advance == 1
    assert len(result.drifted_ships) == 0

    # Turn 4: no advance (should drift again)
    ships, result = check_and_apply_drift(ships, {"ship1": False}, WindDirection.N, 25, 20, 4)
    assert ships["ship1"].turns_without_bow_advance == 0
    assert len(result.drifted_ships) == 1


def test_check_and_apply_drift_preserves_other_ship_attributes():
    """Drift operations don't modify other ship attributes."""
    ship = create_test_ship(turns_without_bow_advance=1)
    original_hull = ship.hull
    original_crew = ship.crew
    original_facing = ship.facing
    ships = {"ship1": ship}

    updated_ships, result = check_and_apply_drift(
        ships, {"ship1": False}, WindDirection.N, 25, 20, 1
    )

    assert updated_ships["ship1"].hull == original_hull
    assert updated_ships["ship1"].crew == original_crew
    assert updated_ships["ship1"].facing == original_facing
