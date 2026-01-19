"""Tests for broadside arc calculation."""

from wsim_core.engine.arc import (
    get_broadside_arc_hexes,
    hex_distance,
    is_hex_in_broadside_arc,
)
from wsim_core.models.common import Broadside, Facing, LoadState, Side
from wsim_core.models.hex import HexCoord
from wsim_core.models.ship import Ship


def create_test_ship(
    ship_id: str = "test_ship",
    bow_col: int = 10,
    bow_row: int = 10,
    facing: Facing = Facing.N,
) -> Ship:
    """Create a test ship with minimal required fields."""
    from wsim_core.engine.movement_executor import calculate_stern_from_bow

    bow = HexCoord(col=bow_col, row=bow_row)
    stern = calculate_stern_from_bow(bow, facing)

    return Ship(
        id=ship_id,
        name="Test Ship",
        side=Side.P1,
        bow_hex=bow,
        stern_hex=stern,
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
    )


class TestHexDistance:
    """Tests for hex distance calculation."""

    def test_distance_same_hex(self) -> None:
        """Distance to same hex is 0."""
        hex1 = HexCoord(col=5, row=5)
        assert hex_distance(hex1, hex1) == 0

    def test_distance_adjacent_hex(self) -> None:
        """Distance to adjacent hex is 1."""
        hex1 = HexCoord(col=5, row=5)
        hex2 = HexCoord(col=5, row=4)  # North
        assert hex_distance(hex1, hex2) == 1

    def test_distance_two_hexes(self) -> None:
        """Distance of two hexes apart."""
        hex1 = HexCoord(col=5, row=5)
        hex2 = HexCoord(col=5, row=3)  # Two hexes north
        assert hex_distance(hex1, hex2) == 2

    def test_distance_diagonal(self) -> None:
        """Distance calculation works for diagonal movement."""
        hex1 = HexCoord(col=5, row=5)
        hex2 = HexCoord(col=7, row=5)  # Two columns east
        assert hex_distance(hex1, hex2) == 2

    def test_distance_symmetric(self) -> None:
        """Distance is symmetric (same in both directions)."""
        hex1 = HexCoord(col=3, row=7)
        hex2 = HexCoord(col=8, row=4)
        assert hex_distance(hex1, hex2) == hex_distance(hex2, hex1)


class TestBroadsideArcHexes:
    """Tests for broadside arc hex calculation."""

    def test_arc_excludes_ship_position(self) -> None:
        """Arc should not include the ship's own position."""
        ship = create_test_ship(bow_col=10, bow_row=10, facing=Facing.N)
        arc_hexes = get_broadside_arc_hexes(ship, Broadside.L, max_range=5)

        assert ship.bow_hex not in arc_hexes

    def test_arc_contains_perpendicular_hexes(self) -> None:
        """Arc should contain hexes perpendicular to ship facing."""
        ship = create_test_ship(bow_col=10, bow_row=10, facing=Facing.N)

        # Left broadside should fire to the west (port)
        left_arc = get_broadside_arc_hexes(ship, Broadside.L, max_range=3)

        # Should include hexes to the west
        assert HexCoord(col=9, row=10) in left_arc  # West
        assert HexCoord(col=8, row=10) in left_arc  # Further west

        # Right broadside should fire to the east (starboard)
        right_arc = get_broadside_arc_hexes(ship, Broadside.R, max_range=3)

        # Should include hexes to the east
        assert HexCoord(col=11, row=10) in right_arc  # East
        assert HexCoord(col=12, row=10) in right_arc  # Further east

    def test_arc_respects_max_range(self) -> None:
        """Arc should only extend to max_range."""
        ship = create_test_ship(bow_col=10, bow_row=10, facing=Facing.N)

        # Test with small range
        arc_hexes = get_broadside_arc_hexes(ship, Broadside.L, max_range=2)

        # Should not include hexes beyond range 2
        # Count unique hexes - should be reasonable for range 2
        assert len(arc_hexes) > 0
        assert len(arc_hexes) < 20  # Sanity check

    def test_arc_left_vs_right_different(self) -> None:
        """Left and right arcs should be different and not overlap (mostly)."""
        ship = create_test_ship(bow_col=10, bow_row=10, facing=Facing.E)

        left_arc = get_broadside_arc_hexes(ship, Broadside.L, max_range=3)
        right_arc = get_broadside_arc_hexes(ship, Broadside.R, max_range=3)

        # Arcs should have some elements
        assert len(left_arc) > 0
        assert len(right_arc) > 0

        # Most hexes should be different (some overlap at extreme angles is OK)
        overlap = left_arc & right_arc
        assert len(overlap) < min(len(left_arc), len(right_arc)) * 0.3  # Less than 30% overlap

    def test_arc_facing_north_left_fires_west(self) -> None:
        """Ship facing north should have left broadside firing west."""
        ship = create_test_ship(bow_col=10, bow_row=10, facing=Facing.N)
        arc = get_broadside_arc_hexes(ship, Broadside.L, max_range=5)

        # Should include hexes to the west
        assert any(h.col < ship.bow_hex.col for h in arc)

    def test_arc_facing_north_right_fires_east(self) -> None:
        """Ship facing north should have right broadside firing east."""
        ship = create_test_ship(bow_col=10, bow_row=10, facing=Facing.N)
        arc = get_broadside_arc_hexes(ship, Broadside.R, max_range=5)

        # Should include hexes to the east
        assert any(h.col > ship.bow_hex.col for h in arc)

    def test_arc_facing_east_left_fires_north(self) -> None:
        """Ship facing east should have left broadside firing north."""
        ship = create_test_ship(bow_col=10, bow_row=10, facing=Facing.E)
        arc = get_broadside_arc_hexes(ship, Broadside.L, max_range=5)

        # Should include hexes to the north
        assert any(h.row < ship.bow_hex.row for h in arc)

    def test_arc_facing_east_right_fires_south(self) -> None:
        """Ship facing east should have right broadside firing south."""
        ship = create_test_ship(bow_col=10, bow_row=10, facing=Facing.E)
        arc = get_broadside_arc_hexes(ship, Broadside.R, max_range=5)

        # Should include hexes to the south
        assert any(h.row > ship.bow_hex.row for h in arc)

    def test_arc_all_facings_produce_arcs(self) -> None:
        """All facings should produce valid arcs for both broadsides."""
        all_facings = [
            Facing.N,
            Facing.NE,
            Facing.E,
            Facing.SE,
            Facing.S,
            Facing.SW,
            Facing.W,
            Facing.NW,
        ]

        for facing in all_facings:
            ship = create_test_ship(bow_col=10, bow_row=10, facing=facing)

            left_arc = get_broadside_arc_hexes(ship, Broadside.L, max_range=3)
            right_arc = get_broadside_arc_hexes(ship, Broadside.R, max_range=3)

            assert len(left_arc) > 0, f"Left arc empty for facing {facing}"
            assert len(right_arc) > 0, f"Right arc empty for facing {facing}"


class TestIsHexInBroadsideArc:
    """Tests for checking if a hex is in a broadside arc."""

    def test_hex_in_arc_returns_true(self) -> None:
        """Hex clearly in arc should return True."""
        ship = create_test_ship(bow_col=10, bow_row=10, facing=Facing.N)
        target = HexCoord(col=8, row=10)  # West of ship

        assert is_hex_in_broadside_arc(ship, target, Broadside.L, max_range=5)

    def test_hex_out_of_arc_returns_false(self) -> None:
        """Hex clearly not in arc should return False."""
        ship = create_test_ship(bow_col=10, bow_row=10, facing=Facing.N)
        target = HexCoord(col=10, row=5)  # Directly ahead (north) of ship

        # Directly ahead is not in broadside arc
        assert not is_hex_in_broadside_arc(ship, target, Broadside.L, max_range=10)

    def test_hex_beyond_range_returns_false(self) -> None:
        """Hex beyond max range should return False."""
        ship = create_test_ship(bow_col=10, bow_row=10, facing=Facing.N)
        target = HexCoord(col=2, row=10)  # 8 hexes west

        # Within arc direction but beyond range
        assert not is_hex_in_broadside_arc(ship, target, Broadside.L, max_range=5)

    def test_ship_own_position_returns_false(self) -> None:
        """Ship's own position should not be in arc."""
        ship = create_test_ship(bow_col=10, bow_row=10, facing=Facing.N)

        assert not is_hex_in_broadside_arc(ship, ship.bow_hex, Broadside.L, max_range=10)
        assert not is_hex_in_broadside_arc(ship, ship.bow_hex, Broadside.R, max_range=10)

    def test_opposite_broadside_different_targets(self) -> None:
        """A hex in left arc should generally not be in right arc."""
        ship = create_test_ship(bow_col=10, bow_row=10, facing=Facing.N)
        target_west = HexCoord(col=7, row=10)  # West
        target_east = HexCoord(col=13, row=10)  # East

        # West target in left arc, not right
        assert is_hex_in_broadside_arc(ship, target_west, Broadside.L, max_range=5)
        assert not is_hex_in_broadside_arc(ship, target_west, Broadside.R, max_range=5)

        # East target in right arc, not left
        assert is_hex_in_broadside_arc(ship, target_east, Broadside.R, max_range=5)
        assert not is_hex_in_broadside_arc(ship, target_east, Broadside.L, max_range=5)

    def test_arc_check_various_facings(self) -> None:
        """Arc check should work correctly for various ship facings."""
        # Ship facing east
        ship = create_test_ship(bow_col=10, bow_row=10, facing=Facing.E)

        # North should be in left arc
        target_north = HexCoord(col=10, row=7)
        assert is_hex_in_broadside_arc(ship, target_north, Broadside.L, max_range=5)

        # South should be in right arc
        target_south = HexCoord(col=10, row=13)
        assert is_hex_in_broadside_arc(ship, target_south, Broadside.R, max_range=5)

        # Directly ahead (east) should not be in either broadside
        target_ahead = HexCoord(col=15, row=10)
        assert not is_hex_in_broadside_arc(ship, target_ahead, Broadside.L, max_range=10)
        assert not is_hex_in_broadside_arc(ship, target_ahead, Broadside.R, max_range=10)

    def test_arc_check_with_default_range(self) -> None:
        """Arc check should work with default max_range."""
        ship = create_test_ship(bow_col=10, bow_row=10, facing=Facing.N)
        target = HexCoord(col=5, row=10)  # 5 hexes west

        # Should work with default range (10)
        assert is_hex_in_broadside_arc(ship, target, Broadside.L)  # Use default max_range
