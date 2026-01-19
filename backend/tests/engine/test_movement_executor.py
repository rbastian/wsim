"""Tests for movement execution engine."""

import pytest

from wsim_core.engine import (
    MovementExecutionError,
    calculate_stern_from_bow,
    execute_ship_forward_movement,
    execute_ship_turn,
    execute_simultaneous_movement,
    get_adjacent_hex,
    parse_movement,
    turn_left,
    turn_right,
)
from wsim_core.engine.movement_parser import MovementActionType
from wsim_core.models.common import Facing, LoadState, Side
from wsim_core.models.hex import HexCoord
from wsim_core.models.ship import Ship

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_ship() -> Ship:
    """Create a sample ship for testing."""
    return Ship(
        id="test_ship_1",
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


# ============================================================================
# Hex Geometry Tests
# ============================================================================


def test_turn_left_from_north():
    """Test turning left from north goes to northwest."""
    assert turn_left(Facing.N) == Facing.NW


def test_turn_left_full_rotation():
    """Test a full left rotation returns to original facing."""
    facing = Facing.N
    for _ in range(8):  # 8 facings * 45 degrees each = 360 degrees
        facing = turn_left(facing)
    assert facing == Facing.N


def test_turn_right_from_north():
    """Test turning right from north goes to northeast."""
    assert turn_right(Facing.N) == Facing.NE


def test_turn_right_full_rotation():
    """Test a full right rotation returns to original facing."""
    facing = Facing.N
    for _ in range(8):  # 8 facings * 45 degrees each = 360 degrees
        facing = turn_right(facing)
    assert facing == Facing.N


def test_turn_left_all_facings():
    """Test turn_left for all 8 facings."""
    expected = {
        Facing.N: Facing.NW,
        Facing.NE: Facing.N,
        Facing.E: Facing.NE,
        Facing.SE: Facing.E,
        Facing.S: Facing.SE,
        Facing.SW: Facing.S,
        Facing.W: Facing.SW,
        Facing.NW: Facing.W,
    }
    for facing, expected_result in expected.items():
        assert turn_left(facing) == expected_result


def test_turn_right_all_facings():
    """Test turn_right for all 8 facings."""
    expected = {
        Facing.N: Facing.NE,
        Facing.NE: Facing.E,
        Facing.E: Facing.SE,
        Facing.SE: Facing.S,
        Facing.S: Facing.SW,
        Facing.SW: Facing.W,
        Facing.W: Facing.NW,
        Facing.NW: Facing.N,
    }
    for facing, expected_result in expected.items():
        assert turn_right(facing) == expected_result


def test_get_adjacent_hex_north_even_col():
    """Test getting adjacent hex to the north from even column."""
    hex_coord = HexCoord(col=10, row=10)
    adjacent = get_adjacent_hex(hex_coord, Facing.N)
    assert adjacent == HexCoord(col=10, row=9)


def test_get_adjacent_hex_north_odd_col():
    """Test getting adjacent hex to the north from odd column."""
    hex_coord = HexCoord(col=11, row=10)
    adjacent = get_adjacent_hex(hex_coord, Facing.N)
    assert adjacent == HexCoord(col=11, row=9)


def test_get_adjacent_hex_all_directions_even_col():
    """Test getting adjacent hexes in all directions from even column."""
    hex_coord = HexCoord(col=10, row=10)
    expected = {
        Facing.N: HexCoord(col=10, row=9),
        Facing.NE: HexCoord(col=11, row=9),
        Facing.SE: HexCoord(col=11, row=10),
        Facing.S: HexCoord(col=10, row=11),
        Facing.SW: HexCoord(col=9, row=10),
        Facing.NW: HexCoord(col=9, row=9),
        Facing.E: HexCoord(col=11, row=10),
        Facing.W: HexCoord(col=9, row=10),
    }
    for direction, expected_hex in expected.items():
        adjacent = get_adjacent_hex(hex_coord, direction)
        assert adjacent == expected_hex, f"Failed for direction {direction}"


def test_get_adjacent_hex_all_directions_odd_col():
    """Test getting adjacent hexes in all directions from odd column."""
    hex_coord = HexCoord(col=11, row=10)
    expected = {
        Facing.N: HexCoord(col=11, row=9),
        Facing.NE: HexCoord(col=12, row=10),
        Facing.SE: HexCoord(col=12, row=11),
        Facing.S: HexCoord(col=11, row=11),
        Facing.SW: HexCoord(col=10, row=11),
        Facing.NW: HexCoord(col=10, row=10),
        Facing.E: HexCoord(col=12, row=10),
        Facing.W: HexCoord(col=10, row=10),
    }
    for direction, expected_hex in expected.items():
        adjacent = get_adjacent_hex(hex_coord, direction)
        assert adjacent == expected_hex, f"Failed for direction {direction}"


def test_calculate_stern_from_bow_north():
    """Test calculating stern when facing north."""
    bow = HexCoord(col=10, row=10)
    stern = calculate_stern_from_bow(bow, Facing.N)
    assert stern == HexCoord(col=10, row=11)


def test_calculate_stern_from_bow_all_facings_even_col():
    """Test calculating stern for all facings from even column."""
    bow = HexCoord(col=10, row=10)
    expected = {
        Facing.N: HexCoord(col=10, row=11),
        Facing.NE: HexCoord(col=9, row=10),
        Facing.SE: HexCoord(col=9, row=9),
        Facing.S: HexCoord(col=10, row=9),
        Facing.SW: HexCoord(col=11, row=9),
        Facing.NW: HexCoord(col=11, row=10),
        Facing.E: HexCoord(col=9, row=10),
        Facing.W: HexCoord(col=11, row=10),
    }
    for facing, expected_stern in expected.items():
        stern = calculate_stern_from_bow(bow, facing)
        assert stern == expected_stern, f"Failed for facing {facing}"


def test_calculate_stern_from_bow_all_facings_odd_col():
    """Test calculating stern for all facings from odd column."""
    bow = HexCoord(col=11, row=10)
    expected = {
        Facing.N: HexCoord(col=11, row=11),
        Facing.NE: HexCoord(col=10, row=11),
        Facing.SE: HexCoord(col=10, row=10),
        Facing.S: HexCoord(col=11, row=9),
        Facing.SW: HexCoord(col=12, row=10),
        Facing.NW: HexCoord(col=12, row=11),
        Facing.E: HexCoord(col=10, row=10),
        Facing.W: HexCoord(col=12, row=10),
    }
    for facing, expected_stern in expected.items():
        stern = calculate_stern_from_bow(bow, facing)
        assert stern == expected_stern, f"Failed for facing {facing}"


# ============================================================================
# Ship Turn Tests
# ============================================================================


def test_execute_ship_turn_left(sample_ship: Ship):
    """Test executing a left turn."""
    updated_ship = execute_ship_turn(sample_ship, MovementActionType.TURN_LEFT)
    assert updated_ship.facing == Facing.NW
    # Position should not change
    assert updated_ship.bow_hex == sample_ship.bow_hex
    # Stern should be recalculated based on new facing
    expected_stern = calculate_stern_from_bow(sample_ship.bow_hex, Facing.NW)
    assert updated_ship.stern_hex == expected_stern


def test_execute_ship_turn_right(sample_ship: Ship):
    """Test executing a right turn."""
    updated_ship = execute_ship_turn(sample_ship, MovementActionType.TURN_RIGHT)
    assert updated_ship.facing == Facing.NE
    assert updated_ship.bow_hex == sample_ship.bow_hex
    expected_stern = calculate_stern_from_bow(sample_ship.bow_hex, Facing.NE)
    assert updated_ship.stern_hex == expected_stern


def test_execute_ship_turn_invalid_direction(sample_ship: Ship):
    """Test that invalid turn direction raises error."""
    with pytest.raises(MovementExecutionError, match="Invalid turn direction"):
        execute_ship_turn(sample_ship, MovementActionType.MOVE_FORWARD)


def test_execute_ship_turn_sequence(sample_ship: Ship):
    """Test a sequence of turns."""
    ship = sample_ship
    # Turn left twice from N: N -> NW -> W
    ship = execute_ship_turn(ship, MovementActionType.TURN_LEFT)
    ship = execute_ship_turn(ship, MovementActionType.TURN_LEFT)
    assert ship.facing == Facing.W


# ============================================================================
# Ship Forward Movement Tests
# ============================================================================


def test_execute_ship_forward_movement_one_hex(sample_ship: Ship):
    """Test moving forward one hex."""
    updated_ship = execute_ship_forward_movement(sample_ship, 1, map_width=25, map_height=20)
    # Facing north, so bow moves from (10,10) to (10,9)
    assert updated_ship.bow_hex == HexCoord(col=10, row=9)
    # Stern should follow
    expected_stern = calculate_stern_from_bow(updated_ship.bow_hex, sample_ship.facing)
    assert updated_ship.stern_hex == expected_stern


def test_execute_ship_forward_movement_multiple_hexes(sample_ship: Ship):
    """Test moving forward multiple hexes."""
    updated_ship = execute_ship_forward_movement(sample_ship, 3, map_width=25, map_height=20)
    assert updated_ship.bow_hex == HexCoord(col=10, row=7)


def test_execute_ship_forward_movement_zero_distance(sample_ship: Ship):
    """Test that zero distance movement returns unchanged ship."""
    updated_ship = execute_ship_forward_movement(sample_ship, 0, map_width=25, map_height=20)
    assert updated_ship.bow_hex == sample_ship.bow_hex
    assert updated_ship.stern_hex == sample_ship.stern_hex


def test_execute_ship_forward_movement_out_of_bounds_north(sample_ship: Ship):
    """Test that movement out of bounds raises error."""
    # Start at row 10, move 15 hexes north should go out of bounds (row < 0)
    with pytest.raises(MovementExecutionError, match="out of bounds"):
        execute_ship_forward_movement(sample_ship, 15, map_width=25, map_height=20)


def test_execute_ship_forward_movement_out_of_bounds_south():
    """Test that movement out of bounds south raises error."""
    ship = Ship(
        id="test",
        name="Test",
        side=Side.P1,
        bow_hex=HexCoord(col=10, row=15),
        stern_hex=HexCoord(col=10, row=14),
        facing=Facing.S,
        battle_sail_speed=10,
        guns_L=10,
        guns_R=10,
        hull=12,
        rigging=10,
        crew=10,
        marines=2,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
    )
    with pytest.raises(MovementExecutionError, match="out of bounds"):
        execute_ship_forward_movement(ship, 10, map_width=25, map_height=20)


# ============================================================================
# Simultaneous Movement Tests
# ============================================================================


def test_execute_simultaneous_movement_single_ship_forward():
    """Test simultaneous movement with single ship moving forward."""
    ship = Ship(
        id="ship1",
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

    parsed = parse_movement("2")
    movements = {"ship1": parsed}
    ships = {"ship1": ship}

    updated_ships, result = execute_simultaneous_movement(ships, movements, 25, 20)

    assert updated_ships["ship1"].bow_hex == HexCoord(col=10, row=8)
    assert result.ships_moved["ship1"] is True
    assert result.total_actions_executed == 1


def test_execute_simultaneous_movement_single_ship_turn_and_move():
    """Test simultaneous movement with turns and forward movement."""
    ship = Ship(
        id="ship1",
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

    parsed = parse_movement("L1")
    movements = {"ship1": parsed}
    ships = {"ship1": ship}

    updated_ships, result = execute_simultaneous_movement(ships, movements, 25, 20)

    # After turn left, facing is NW
    assert updated_ships["ship1"].facing == Facing.NW
    # After moving 1 hex NW from (10, 10) even col: (9, 9)
    assert updated_ships["ship1"].bow_hex == HexCoord(col=9, row=9)
    assert result.ships_moved["ship1"] is True


def test_execute_simultaneous_movement_single_ship_no_movement():
    """Test simultaneous movement with no movement action."""
    ship = Ship(
        id="ship1",
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

    parsed = parse_movement("0")
    movements = {"ship1": parsed}
    ships = {"ship1": ship}

    updated_ships, result = execute_simultaneous_movement(ships, movements, 25, 20)

    assert updated_ships["ship1"].bow_hex == ship.bow_hex
    assert updated_ships["ship1"].facing == ship.facing
    assert result.ships_moved["ship1"] is False


def test_execute_simultaneous_movement_multiple_ships():
    """Test simultaneous movement with multiple ships."""
    ship1 = Ship(
        id="ship1",
        name="Ship 1",
        side=Side.P1,
        bow_hex=HexCoord(col=5, row=10),
        stern_hex=HexCoord(col=5, row=11),
        facing=Facing.N,
        battle_sail_speed=3,
        guns_L=10,
        guns_R=10,
        hull=12,
        rigging=10,
        crew=10,
        marines=2,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
    )

    ship2 = Ship(
        id="ship2",
        name="Ship 2",
        side=Side.P2,
        bow_hex=HexCoord(col=15, row=10),
        stern_hex=HexCoord(col=15, row=9),
        facing=Facing.S,
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

    parsed1 = parse_movement("2")
    parsed2 = parse_movement("R1")

    movements = {"ship1": parsed1, "ship2": parsed2}
    ships = {"ship1": ship1, "ship2": ship2}

    updated_ships, result = execute_simultaneous_movement(ships, movements, 25, 20)

    # Ship 1 moves 2 hexes north
    assert updated_ships["ship1"].bow_hex == HexCoord(col=5, row=8)
    # Ship 2 turns right (to SW) then moves 1
    assert updated_ships["ship2"].facing == Facing.SW
    assert result.ships_moved["ship1"] is True
    assert result.ships_moved["ship2"] is True


def test_execute_simultaneous_movement_exceeds_battle_sail_speed():
    """Test that exceeding battle sail speed raises error."""
    ship = Ship(
        id="ship1",
        name="Ship 1",
        side=Side.P1,
        bow_hex=HexCoord(col=10, row=10),
        stern_hex=HexCoord(col=10, row=11),
        facing=Facing.N,
        battle_sail_speed=3,
        guns_L=10,
        guns_R=10,
        hull=12,
        rigging=10,
        crew=10,
        marines=2,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
    )

    parsed = parse_movement("4")  # Exceeds battle_sail_speed of 3
    movements = {"ship1": parsed}
    ships = {"ship1": ship}

    with pytest.raises(MovementExecutionError, match="exceeds battle sail speed"):
        execute_simultaneous_movement(ships, movements, 25, 20)


def test_execute_simultaneous_movement_ship_not_found():
    """Test that missing ship raises error."""
    parsed = parse_movement("1")
    movements = {"nonexistent_ship": parsed}
    ships = {}

    with pytest.raises(MovementExecutionError, match="not found"):
        execute_simultaneous_movement(ships, movements, 25, 20)


def test_execute_simultaneous_movement_turn_only_no_bow_advance():
    """Test that turning only does not advance bow."""
    ship = Ship(
        id="ship1",
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

    parsed = parse_movement("LR")  # Just turns, no forward movement
    movements = {"ship1": parsed}
    ships = {"ship1": ship}

    updated_ships, result = execute_simultaneous_movement(ships, movements, 25, 20)

    # Bow position unchanged
    assert updated_ships["ship1"].bow_hex == ship.bow_hex
    assert result.ships_moved["ship1"] is False


def test_execute_simultaneous_movement_complex_sequence():
    """Test complex movement sequence."""
    ship = Ship(
        id="ship1",
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

    parsed = parse_movement("L1R2")
    movements = {"ship1": parsed}
    ships = {"ship1": ship}

    updated_ships, result = execute_simultaneous_movement(ships, movements, 25, 20)

    # Should complete all actions
    assert result.ships_moved["ship1"] is True
    # Total forward movement should be 1 + 2 = 3
    assert result.total_actions_executed == 4  # L, 1, R, 2


def test_execute_simultaneous_movement_preserves_ship_attributes():
    """Test that movement preserves non-position ship attributes."""
    ship = Ship(
        id="ship1",
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
        struck=False,
        turns_without_bow_advance=1,
    )

    parsed = parse_movement("1")
    movements = {"ship1": parsed}
    ships = {"ship1": ship}

    updated_ships, result = execute_simultaneous_movement(ships, movements, 25, 20)

    # Non-position attributes should be preserved
    assert updated_ships["ship1"].id == ship.id
    assert updated_ships["ship1"].name == ship.name
    assert updated_ships["ship1"].side == ship.side
    assert updated_ships["ship1"].battle_sail_speed == ship.battle_sail_speed
    assert updated_ships["ship1"].guns_L == ship.guns_L
    assert updated_ships["ship1"].guns_R == ship.guns_R
    assert updated_ships["ship1"].hull == ship.hull
    assert updated_ships["ship1"].rigging == ship.rigging
    assert updated_ships["ship1"].crew == ship.crew
    assert updated_ships["ship1"].marines == ship.marines
    assert updated_ships["ship1"].load_L == ship.load_L
    assert updated_ships["ship1"].load_R == ship.load_R
    assert updated_ships["ship1"].fouled == ship.fouled
    assert updated_ships["ship1"].struck == ship.struck
    assert updated_ships["ship1"].turns_without_bow_advance == ship.turns_without_bow_advance
