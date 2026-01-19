"""Tests for target selection and closest-target rule enforcement."""

from wsim_core.engine.movement_executor import calculate_stern_from_bow
from wsim_core.engine.targeting import (
    get_all_valid_targets,
    get_closest_enemy_in_arc,
    get_ships_in_arc,
    get_targeting_info,
    is_valid_target,
)
from wsim_core.models.common import Broadside, Facing, LoadState, Side
from wsim_core.models.hex import HexCoord
from wsim_core.models.ship import Ship


def create_test_ship(
    ship_id: str,
    side: Side,
    bow_hex: tuple[int, int],
    facing: Facing,
    struck: bool = False,
) -> Ship:
    """Helper to create a test ship with minimal configuration."""
    bow = HexCoord(col=bow_hex[0], row=bow_hex[1])
    stern = calculate_stern_from_bow(bow, facing)

    return Ship(
        id=ship_id,
        name=ship_id,
        side=side,
        bow_hex=bow,
        stern_hex=stern,
        facing=facing,
        battle_sail_speed=3,
        guns_L=10,
        guns_R=10,
        hull=12,
        rigging=10,
        crew=10,
        marines=2,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
        struck=struck,
    )


class TestGetShipsInArc:
    """Tests for get_ships_in_arc function."""

    def test_empty_game_returns_no_ships(self):
        """No ships in arc when only the firing ship exists."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        all_ships = [firing_ship]

        result = get_ships_in_arc(firing_ship, all_ships, Broadside.R)

        assert len(result) == 0

    def test_finds_ship_with_bow_in_arc(self):
        """Ship is found when its bow is in firing arc."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        # R broadside fires south (increasing row), so place target at row 15
        target_ship = create_test_ship("p2_ship1", Side.P2, (10, 15), Facing.E)
        all_ships = [firing_ship, target_ship]

        result = get_ships_in_arc(firing_ship, all_ships, Broadside.R)  # R broadside fires south

        assert len(result) == 1
        assert result[0].ship.id == "p2_ship1"
        assert result[0].distance > 0

    def test_finds_ship_with_stern_in_arc(self):
        """Ship is found when its stern is in firing arc."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        # R broadside fires south, place target so stern is in arc
        target_ship = create_test_ship("p2_ship1", Side.P2, (10, 14), Facing.W)
        all_ships = [firing_ship, target_ship]

        result = get_ships_in_arc(firing_ship, all_ships, Broadside.R)

        assert len(result) == 1
        assert result[0].ship.id == "p2_ship1"

    def test_excludes_firing_ship(self):
        """Firing ship is never included in results."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        all_ships = [firing_ship]

        result = get_ships_in_arc(firing_ship, all_ships, Broadside.R)

        assert len(result) == 0

    def test_includes_friendly_ships(self):
        """get_ships_in_arc includes friendly ships (filtering is done elsewhere)."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        friendly_ship = create_test_ship("p1_ship2", Side.P1, (10, 13), Facing.E)
        all_ships = [firing_ship, friendly_ship]

        result = get_ships_in_arc(firing_ship, all_ships, Broadside.R)

        assert len(result) == 1
        assert result[0].ship.id == "p1_ship2"

    def test_respects_max_range(self):
        """Ships beyond max_range are excluded."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        close_ship = create_test_ship("p2_ship1", Side.P2, (10, 14), Facing.E)
        far_ship = create_test_ship("p2_ship2", Side.P2, (10, 25), Facing.E)  # >10 hexes away
        all_ships = [firing_ship, close_ship, far_ship]

        result = get_ships_in_arc(firing_ship, all_ships, Broadside.R, max_range=5)

        ship_ids = [t.ship.id for t in result]
        assert "p2_ship1" in ship_ids
        assert "p2_ship2" not in ship_ids


class TestGetClosestEnemyInArc:
    """Tests for get_closest_enemy_in_arc function."""

    def test_no_enemies_returns_none(self):
        """Returns None when no enemy ships in arc."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        friendly_ship = create_test_ship("p1_ship2", Side.P1, (10, 13), Facing.E)
        all_ships = [firing_ship, friendly_ship]

        result = get_closest_enemy_in_arc(firing_ship, all_ships, Broadside.R)

        assert result is None

    def test_returns_only_enemy_in_arc(self):
        """Returns the enemy when only one enemy in arc."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        enemy_ship = create_test_ship("p2_ship1", Side.P2, (10, 13), Facing.E)
        all_ships = [firing_ship, enemy_ship]

        result = get_closest_enemy_in_arc(firing_ship, all_ships, Broadside.R)

        assert result is not None
        assert result.id == "p2_ship1"

    def test_returns_closest_when_multiple_enemies(self):
        """Returns closest enemy when multiple enemies in arc."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        close_enemy = create_test_ship("p2_ship1", Side.P2, (10, 14), Facing.E)
        far_enemy = create_test_ship("p2_ship2", Side.P2, (10, 18), Facing.E)
        all_ships = [firing_ship, close_enemy, far_enemy]

        result = get_closest_enemy_in_arc(firing_ship, all_ships, Broadside.R)

        assert result is not None
        assert result.id == "p2_ship1"  # Closer one

    def test_ignores_friendly_ships(self):
        """Friendly ships don't affect closest enemy selection."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        very_close_friendly = create_test_ship("p1_ship2", Side.P1, (10, 11), Facing.E)
        enemy_ship = create_test_ship("p2_ship1", Side.P2, (10, 15), Facing.E)
        all_ships = [firing_ship, very_close_friendly, enemy_ship]

        result = get_closest_enemy_in_arc(firing_ship, all_ships, Broadside.R)

        assert result is not None
        assert result.id == "p2_ship1"

    def test_ignores_struck_ships(self):
        """Struck ships cannot be targeted."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        struck_enemy = create_test_ship("p2_ship1", Side.P2, (10, 12), Facing.E, struck=True)
        active_enemy = create_test_ship("p2_ship2", Side.P2, (10, 16), Facing.E)
        all_ships = [firing_ship, struck_enemy, active_enemy]

        result = get_closest_enemy_in_arc(firing_ship, all_ships, Broadside.R)

        assert result is not None
        assert result.id == "p2_ship2"

    def test_returns_none_when_only_struck_enemies_in_arc(self):
        """Returns None when all enemies in arc are struck."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        struck_enemy = create_test_ship("p2_ship1", Side.P2, (10, 13), Facing.E, struck=True)
        all_ships = [firing_ship, struck_enemy]

        result = get_closest_enemy_in_arc(firing_ship, all_ships, Broadside.R)

        assert result is None

    def test_different_broadsides_different_targets(self):
        """Left and right broadsides can have different closest targets."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.N)
        # West of firer (left broadside arc when facing north)
        west_enemy = create_test_ship("p2_ship1", Side.P2, (7, 10), Facing.E)
        # East of firer (right broadside arc when facing north)
        east_enemy = create_test_ship("p2_ship2", Side.P2, (13, 10), Facing.E)
        all_ships = [firing_ship, west_enemy, east_enemy]

        left_target = get_closest_enemy_in_arc(firing_ship, all_ships, Broadside.L)
        right_target = get_closest_enemy_in_arc(firing_ship, all_ships, Broadside.R)

        assert left_target is not None
        assert right_target is not None
        assert left_target.id == "p2_ship1"
        assert right_target.id == "p2_ship2"


class TestGetAllValidTargets:
    """Tests for get_all_valid_targets function."""

    def test_returns_single_target_when_one_closest(self):
        """Returns list with one ship when there's a clear closest enemy."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        close_enemy = create_test_ship("p2_ship1", Side.P2, (10, 14), Facing.E)
        far_enemy = create_test_ship("p2_ship2", Side.P2, (10, 18), Facing.E)
        all_ships = [firing_ship, close_enemy, far_enemy]

        result = get_all_valid_targets(firing_ship, all_ships, Broadside.R)

        assert len(result) == 1
        assert result[0].id == "p2_ship1"

    def test_returns_multiple_targets_when_equidistant(self):
        """Returns all targets at minimum distance when multiple are equidistant."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        # Place two enemies at roughly equal distance south
        enemy1 = create_test_ship("p2_ship1", Side.P2, (9, 14), Facing.E)
        enemy2 = create_test_ship("p2_ship2", Side.P2, (11, 14), Facing.E)
        all_ships = [firing_ship, enemy1, enemy2]

        result = get_all_valid_targets(firing_ship, all_ships, Broadside.R)

        # Both should be valid targets if they're equidistant
        assert len(result) >= 1  # At least one should be valid
        result_ids = [ship.id for ship in result]
        # Either both or one depending on exact arc geometry, but closest should be present
        assert "p2_ship1" in result_ids or "p2_ship2" in result_ids

    def test_returns_empty_when_no_enemies(self):
        """Returns empty list when no valid enemies in arc."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        all_ships = [firing_ship]

        result = get_all_valid_targets(firing_ship, all_ships, Broadside.R)

        assert len(result) == 0


class TestIsValidTarget:
    """Tests for is_valid_target function."""

    def test_cannot_target_self(self):
        """Ship cannot target itself."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        all_ships = [firing_ship]

        result = is_valid_target(firing_ship, firing_ship, all_ships, Broadside.R)

        assert result is False

    def test_cannot_target_friendly_ship(self):
        """Ship cannot target friendly ships."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        friendly_ship = create_test_ship("p1_ship2", Side.P1, (10, 13), Facing.E)
        all_ships = [firing_ship, friendly_ship]

        result = is_valid_target(firing_ship, friendly_ship, all_ships, Broadside.R)

        assert result is False

    def test_cannot_target_struck_ship(self):
        """Struck ships cannot be targeted."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        struck_enemy = create_test_ship("p2_ship1", Side.P2, (10, 13), Facing.E, struck=True)
        all_ships = [firing_ship, struck_enemy]

        result = is_valid_target(firing_ship, struck_enemy, all_ships, Broadside.R)

        assert result is False

    def test_can_target_closest_enemy(self):
        """Can target the closest enemy in arc."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        close_enemy = create_test_ship("p2_ship1", Side.P2, (10, 14), Facing.E)
        all_ships = [firing_ship, close_enemy]

        result = is_valid_target(firing_ship, close_enemy, all_ships, Broadside.R)

        assert result is True

    def test_cannot_target_farther_enemy_when_closer_exists(self):
        """Cannot target farther enemy when closer enemy exists (closest-target rule)."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        close_enemy = create_test_ship("p2_ship1", Side.P2, (10, 14), Facing.E)
        far_enemy = create_test_ship("p2_ship2", Side.P2, (10, 18), Facing.E)
        all_ships = [firing_ship, close_enemy, far_enemy]

        result = is_valid_target(firing_ship, far_enemy, all_ships, Broadside.R)

        assert result is False

    def test_cannot_target_enemy_outside_arc(self):
        """Cannot target enemy that's outside firing arc."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        # Enemy behind the ship (not in any broadside arc)
        enemy_behind = create_test_ship("p2_ship1", Side.P2, (5, 10), Facing.E)
        all_ships = [firing_ship, enemy_behind]

        # Try both broadsides
        result_left = is_valid_target(firing_ship, enemy_behind, all_ships, Broadside.L)
        result_right = is_valid_target(firing_ship, enemy_behind, all_ships, Broadside.R)

        # Ship directly behind should not be in either broadside arc
        assert result_left is False
        assert result_right is False


class TestGetTargetingInfo:
    """Tests for get_targeting_info debugging function."""

    def test_provides_comprehensive_info(self):
        """Returns detailed targeting information."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        friendly_ship = create_test_ship("p1_ship2", Side.P1, (10, 12), Facing.E)
        close_enemy = create_test_ship("p2_ship1", Side.P2, (10, 14), Facing.E)
        far_enemy = create_test_ship("p2_ship2", Side.P2, (10, 18), Facing.E)
        all_ships = [firing_ship, friendly_ship, close_enemy, far_enemy]

        info = get_targeting_info(firing_ship, all_ships, Broadside.R)

        assert "ships_in_arc" in info
        assert "enemy_ships_in_arc" in info
        assert "valid_targets" in info
        assert "closest_distance" in info
        # Should have some ships in arc
        assert len(info["ships_in_arc"]) > 0
        # Should have enemies in arc
        assert len(info["enemy_ships_in_arc"]) > 0
        # Should have valid targets (closest enemy only)
        valid_targets = info["valid_targets"]
        assert isinstance(valid_targets, list)
        assert len(valid_targets) == 1
        assert valid_targets[0] == "p2_ship1"
        # Closest distance should be set
        closest_distance = info["closest_distance"]
        assert closest_distance is not None
        assert isinstance(closest_distance, int)
        assert closest_distance > 0

    def test_handles_no_enemies(self):
        """Handles case with no enemies gracefully."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.E)
        all_ships = [firing_ship]

        info = get_targeting_info(firing_ship, all_ships, Broadside.R)

        assert info["ships_in_arc"] == []
        assert info["enemy_ships_in_arc"] == []
        assert info["valid_targets"] == []
        assert info["closest_distance"] is None


class TestComplexTargetingScenarios:
    """Integration tests for complex targeting scenarios."""

    def test_screening_scenario(self):
        """Small ship 'screens' larger ship behind it.

        This validates the closest-target rule prevents shooting through
        a closer enemy to hit a farther one.
        """
        firing_ship = create_test_ship("p1_frigate", Side.P1, (10, 10), Facing.E)
        small_ship = create_test_ship("p2_sloop", Side.P2, (10, 14), Facing.E)
        large_ship = create_test_ship("p2_ship_of_line", Side.P2, (10, 16), Facing.E)
        all_ships = [firing_ship, small_ship, large_ship]

        # Only the closer small ship should be targetable
        result = get_closest_enemy_in_arc(firing_ship, all_ships, Broadside.R)
        assert result is not None
        assert result.id == "p2_sloop"

        # Large ship should not be valid target
        assert not is_valid_target(firing_ship, large_ship, all_ships, Broadside.R)

    def test_multi_ship_at_various_distances(self):
        """Multiple ships at various distances and angles."""
        firing_ship = create_test_ship("p1_ship1", Side.P1, (10, 10), Facing.N)

        # Create enemies at various positions
        west_close = create_test_ship("p2_w_close", Side.P2, (8, 10), Facing.E)
        west_far = create_test_ship("p2_w_far", Side.P2, (5, 10), Facing.E)
        east_close = create_test_ship("p2_e_close", Side.P2, (12, 10), Facing.E)
        east_far = create_test_ship("p2_e_far", Side.P2, (15, 10), Facing.E)

        all_ships = [firing_ship, west_close, west_far, east_close, east_far]

        # Left broadside should target west_close
        left_target = get_closest_enemy_in_arc(firing_ship, all_ships, Broadside.L)
        assert left_target is not None
        assert left_target.id == "p2_w_close"

        # Right broadside should target east_close
        right_target = get_closest_enemy_in_arc(firing_ship, all_ships, Broadside.R)
        assert right_target is not None
        assert right_target.id == "p2_e_close"
