"""Tests for combat resolution and hit tables."""

import pytest

from wsim_core.engine.combat import (
    HitTables,
    apply_damage,
    can_fire_broadside,
    get_crew_quality_modifier,
    get_legal_targets,
    resolve_broadside_fire,
)
from wsim_core.engine.rng import SeededRNG
from wsim_core.models.common import AimPoint, Broadside, Facing, LoadState, Side
from wsim_core.models.hex import HexCoord
from wsim_core.models.ship import Ship


@pytest.fixture
def hit_tables():
    """Load hit tables for testing."""
    return HitTables()


@pytest.fixture
def firing_ship():
    """Create a test firing ship."""
    return Ship(
        id="test_firing",
        name="HMS Test",
        side=Side.P1,
        bow_hex=HexCoord(col=5, row=5),
        stern_hex=HexCoord(col=5, row=6),
        facing=Facing.E,
        battle_sail_speed=4,
        guns_L=10,
        guns_R=10,
        carronades_L=0,
        carronades_R=0,
        hull=12,
        rigging=10,
        crew=10,
        marines=2,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
    )


@pytest.fixture
def target_ship():
    """Create a test target ship."""
    return Ship(
        id="test_target",
        name="FS Target",
        side=Side.P2,
        bow_hex=HexCoord(col=8, row=5),  # 3 hexes away
        stern_hex=HexCoord(col=8, row=6),
        facing=Facing.W,
        battle_sail_speed=4,
        guns_L=10,
        guns_R=10,
        carronades_L=0,
        carronades_R=0,
        hull=12,
        rigging=10,
        crew=10,
        marines=2,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
    )


class TestHitTables:
    """Test hit table loading and lookups."""

    def test_load_tables(self, hit_tables):
        """Test that hit tables load successfully."""
        assert hit_tables.data is not None
        assert "hit_table" in hit_tables.data
        assert "range_brackets" in hit_tables.data

    def test_range_bracket_short(self, hit_tables):
        """Test short range bracket."""
        assert hit_tables.get_range_bracket(0) == "short"
        assert hit_tables.get_range_bracket(1) == "short"
        assert hit_tables.get_range_bracket(2) == "short"

    def test_range_bracket_medium(self, hit_tables):
        """Test medium range bracket."""
        assert hit_tables.get_range_bracket(3) == "medium"
        assert hit_tables.get_range_bracket(4) == "medium"
        assert hit_tables.get_range_bracket(5) == "medium"

    def test_range_bracket_long(self, hit_tables):
        """Test long range bracket."""
        assert hit_tables.get_range_bracket(6) == "long"
        assert hit_tables.get_range_bracket(7) == "long"
        assert hit_tables.get_range_bracket(10) == "long"

    def test_hits_lookup_hull_short(self, hit_tables):
        """Test hull hit lookup at short range."""
        # From tables: short hull: 6 gives 2 hits, 5 gives 1 hit
        assert hit_tables.get_hits_for_roll(6, "short", AimPoint.HULL) == 2
        assert hit_tables.get_hits_for_roll(5, "short", AimPoint.HULL) == 1
        assert hit_tables.get_hits_for_roll(1, "short", AimPoint.HULL) == 0

    def test_hits_lookup_rigging_short(self, hit_tables):
        """Test rigging hit lookup at short range."""
        # From tables: short rigging: 6 gives 2 hits
        assert hit_tables.get_hits_for_roll(6, "short", AimPoint.RIGGING) == 2
        assert hit_tables.get_hits_for_roll(1, "short", AimPoint.RIGGING) == 0

    def test_crew_casualties_lookup(self, hit_tables):
        """Test crew casualties lookup."""
        # From tables: 6 gives 2 casualties, 4-5 gives 1
        assert hit_tables.get_crew_casualties_for_roll(6) == 2
        assert hit_tables.get_crew_casualties_for_roll(5) == 1
        assert hit_tables.get_crew_casualties_for_roll(4) == 1
        assert hit_tables.get_crew_casualties_for_roll(1) == 0

    def test_gun_damage_short_range(self, hit_tables):
        """Test gun damage at short range."""
        # From tables: short range 6 gives 1 gun damage
        assert hit_tables.get_gun_damage_for_roll(6, at_short_range=True) == 1
        assert hit_tables.get_gun_damage_for_roll(5, at_short_range=True) == 1
        assert hit_tables.get_gun_damage_for_roll(1, at_short_range=True) == 0

    def test_gun_damage_not_short_range(self, hit_tables):
        """Test gun damage at non-short range."""
        # No gun damage beyond short range
        assert hit_tables.get_gun_damage_for_roll(6, at_short_range=False) == 0


class TestCrewQualityModifier:
    """Test crew quality modifier calculation."""

    def test_full_crew(self):
        """Test no modifier at full crew."""
        ship = Ship(
            id="test",
            name="Test",
            side=Side.P1,
            bow_hex=HexCoord(col=0, row=0),
            stern_hex=HexCoord(col=0, row=1),
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
        assert get_crew_quality_modifier(ship, initial_crew=10) == 0

    def test_three_quarters_crew(self):
        """Test no modifier at 75% crew."""
        ship = Ship(
            id="test",
            name="Test",
            side=Side.P1,
            bow_hex=HexCoord(col=0, row=0),
            stern_hex=HexCoord(col=0, row=1),
            facing=Facing.N,
            battle_sail_speed=4,
            guns_L=10,
            guns_R=10,
            hull=12,
            rigging=10,
            crew=8,  # 80% of 10
            marines=2,
            load_L=LoadState.ROUNDSHOT,
            load_R=LoadState.ROUNDSHOT,
        )
        assert get_crew_quality_modifier(ship, initial_crew=10) == 0

    def test_half_crew(self):
        """Test -1 modifier at half crew."""
        ship = Ship(
            id="test",
            name="Test",
            side=Side.P1,
            bow_hex=HexCoord(col=0, row=0),
            stern_hex=HexCoord(col=0, row=1),
            facing=Facing.N,
            battle_sail_speed=4,
            guns_L=10,
            guns_R=10,
            hull=12,
            rigging=10,
            crew=5,  # 50% of 10
            marines=2,
            load_L=LoadState.ROUNDSHOT,
            load_R=LoadState.ROUNDSHOT,
        )
        assert get_crew_quality_modifier(ship, initial_crew=10) == -1

    def test_minimal_crew(self):
        """Test -2 modifier at minimal crew."""
        ship = Ship(
            id="test",
            name="Test",
            side=Side.P1,
            bow_hex=HexCoord(col=0, row=0),
            stern_hex=HexCoord(col=0, row=1),
            facing=Facing.N,
            battle_sail_speed=4,
            guns_L=10,
            guns_R=10,
            hull=12,
            rigging=10,
            crew=3,  # 30% of 10
            marines=2,
            load_L=LoadState.ROUNDSHOT,
            load_R=LoadState.ROUNDSHOT,
        )
        assert get_crew_quality_modifier(ship, initial_crew=10) == -2


class TestCanFireBroadside:
    """Test broadside firing ability checks."""

    def test_can_fire_loaded_broadside(self, firing_ship):
        """Test that loaded broadside can fire."""
        assert can_fire_broadside(firing_ship, Broadside.L) is True
        assert can_fire_broadside(firing_ship, Broadside.R) is True

    def test_cannot_fire_unloaded_broadside(self, firing_ship):
        """Test that unloaded broadside cannot fire."""
        firing_ship.load_L = LoadState.EMPTY
        assert can_fire_broadside(firing_ship, Broadside.L) is False
        assert can_fire_broadside(firing_ship, Broadside.R) is True

    def test_cannot_fire_struck_ship(self, firing_ship):
        """Test that struck ship cannot fire."""
        firing_ship.struck = True
        assert can_fire_broadside(firing_ship, Broadside.L) is False
        assert can_fire_broadside(firing_ship, Broadside.R) is False

    def test_cannot_fire_no_guns(self, firing_ship):
        """Test that ship with no guns cannot fire."""
        firing_ship.guns_L = 0
        assert can_fire_broadside(firing_ship, Broadside.L) is False
        assert can_fire_broadside(firing_ship, Broadside.R) is True


class TestResolveBroadsideFire:
    """Test broadside firing resolution."""

    def test_resolve_fire_medium_range_hull(self, firing_ship, target_ship, hit_tables):
        """Test resolving fire at medium range aiming at hull."""
        # Target is 3 hexes away (medium range)
        # Use seeded RNG for deterministic results
        rng = SeededRNG(42)

        result = resolve_broadside_fire(
            firing_ship=firing_ship,
            target_ship=target_ship,
            broadside=Broadside.R,
            aim=AimPoint.HULL,
            rng=rng,
            hit_tables=hit_tables,
            initial_crew=10,
        )

        # Check basic properties
        assert result.range == 3
        assert result.range_bracket == "medium"
        assert result.hits >= 0
        assert result.crew_casualties >= 0
        assert result.gun_damage == 0  # Not at short range
        assert len(result.die_rolls) > 0
        assert "crew_quality" in result.modifiers_applied

    def test_resolve_fire_short_range_hull(self, firing_ship, target_ship, hit_tables):
        """Test resolving fire at short range aiming at hull."""
        # Move target closer (1 hex away)
        target_ship.bow_hex = HexCoord(col=6, row=5)
        target_ship.stern_hex = HexCoord(col=6, row=6)

        rng = SeededRNG(42)

        result = resolve_broadside_fire(
            firing_ship=firing_ship,
            target_ship=target_ship,
            broadside=Broadside.R,
            aim=AimPoint.HULL,
            rng=rng,
            hit_tables=hit_tables,
            initial_crew=10,
        )

        assert result.range == 1
        assert result.range_bracket == "short"
        # At short range with hull hits, should have gun damage rolls
        if result.hits > 0:
            assert result.gun_damage >= 0

    def test_resolve_fire_rigging(self, firing_ship, target_ship, hit_tables):
        """Test resolving fire aiming at rigging."""
        rng = SeededRNG(42)

        result = resolve_broadside_fire(
            firing_ship=firing_ship,
            target_ship=target_ship,
            broadside=Broadside.R,
            aim=AimPoint.RIGGING,
            rng=rng,
            hit_tables=hit_tables,
            initial_crew=10,
        )

        # Rigging aim should not cause crew casualties or gun damage
        assert result.crew_casualties == 0
        assert result.gun_damage == 0

    def test_fire_with_reduced_crew(self, firing_ship, target_ship, hit_tables):
        """Test firing with reduced crew applies negative modifier."""
        # Reduce crew to half
        firing_ship.crew = 5

        rng = SeededRNG(42)

        result = resolve_broadside_fire(
            firing_ship=firing_ship,
            target_ship=target_ship,
            broadside=Broadside.R,
            aim=AimPoint.HULL,
            rng=rng,
            hit_tables=hit_tables,
            initial_crew=10,
        )

        # Should have crew quality modifier
        assert result.modifiers_applied["crew_quality"] == -1

    def test_fire_deterministic_with_seed(self, firing_ship, target_ship, hit_tables):
        """Test that same seed produces same results."""
        rng1 = SeededRNG(123)
        result1 = resolve_broadside_fire(
            firing_ship=firing_ship,
            target_ship=target_ship,
            broadside=Broadside.R,
            aim=AimPoint.HULL,
            rng=rng1,
            hit_tables=hit_tables,
            initial_crew=10,
        )

        rng2 = SeededRNG(123)
        result2 = resolve_broadside_fire(
            firing_ship=firing_ship,
            target_ship=target_ship,
            broadside=Broadside.R,
            aim=AimPoint.HULL,
            rng=rng2,
            hit_tables=hit_tables,
            initial_crew=10,
        )

        assert result1.hits == result2.hits
        assert result1.crew_casualties == result2.crew_casualties
        assert result1.gun_damage == result2.gun_damage
        assert result1.die_rolls == result2.die_rolls

    def test_fire_left_broadside(self, firing_ship, target_ship, hit_tables):
        """Test firing from left broadside."""
        rng = SeededRNG(42)

        result = resolve_broadside_fire(
            firing_ship=firing_ship,
            target_ship=target_ship,
            broadside=Broadside.L,
            aim=AimPoint.HULL,
            rng=rng,
            hit_tables=hit_tables,
            initial_crew=10,
        )

        # Should use left broadside guns
        assert result.hits >= 0
        # Die rolls should include one per gun (10 guns on left)
        assert len(result.die_rolls) >= 10

    def test_fire_long_range(self, firing_ship, target_ship, hit_tables):
        """Test firing at long range."""
        # Move target far away
        target_ship.bow_hex = HexCoord(col=13, row=5)  # 8 hexes away
        target_ship.stern_hex = HexCoord(col=13, row=6)

        rng = SeededRNG(42)

        result = resolve_broadside_fire(
            firing_ship=firing_ship,
            target_ship=target_ship,
            broadside=Broadside.R,
            aim=AimPoint.HULL,
            rng=rng,
            hit_tables=hit_tables,
            initial_crew=10,
        )

        assert result.range == 8
        assert result.range_bracket == "long"
        # Long range should generally have fewer hits
        assert result.hits >= 0

    def test_no_hits_means_no_casualties(self, firing_ship, target_ship, hit_tables):
        """Test that if no hits occur, there are no crew casualties or gun damage."""

        # Create a scenario likely to produce no hits (very poor rolls)
        # We'll use a custom RNG that always rolls 1
        class AlwaysRollOne(SeededRNG):
            def roll_d6(self) -> int:
                return 1

        rng = AlwaysRollOne(42)

        result = resolve_broadside_fire(
            firing_ship=firing_ship,
            target_ship=target_ship,
            broadside=Broadside.R,
            aim=AimPoint.HULL,
            rng=rng,
            hit_tables=hit_tables,
            initial_crew=10,
        )

        # Rolling all 1s at medium range should produce no hits
        assert result.hits == 0
        assert result.crew_casualties == 0
        assert result.gun_damage == 0


class TestGetLegalTargets:
    """Test closest-target rule and legal target selection."""

    def test_no_enemies_no_targets(self, firing_ship):
        """Test that no enemies means no legal targets."""
        # Only friendly ships
        all_ships = {
            "firing": firing_ship,
            "friendly": Ship(
                id="friendly",
                name="HMS Friendly",
                side=Side.P1,
                bow_hex=HexCoord(col=8, row=5),
                stern_hex=HexCoord(col=8, row=6),
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
            ),
        }

        targets = get_legal_targets(firing_ship, all_ships, Broadside.R)
        assert len(targets) == 0

    def test_enemy_out_of_arc_no_targets(self, firing_ship):
        """Test that enemy out of broadside arc is not a legal target."""
        # Enemy ahead/north (out of right broadside arc)
        # Right broadside for ship facing E fires to starboard (south)
        all_ships = {
            "firing": firing_ship,
            "enemy": Ship(
                id="enemy",
                name="FS Enemy",
                side=Side.P2,
                bow_hex=HexCoord(col=8, row=2),  # North/ahead (out of starboard arc)
                stern_hex=HexCoord(col=8, row=3),
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
            ),
        }

        # Right broadside fires south, enemy is north
        targets = get_legal_targets(firing_ship, all_ships, Broadside.R)
        assert len(targets) == 0

    def test_single_enemy_in_arc(self, firing_ship, target_ship):
        """Test that single enemy in arc is a legal target."""
        all_ships = {"firing": firing_ship, "target": target_ship}

        # Right broadside fires east, target is to the east
        targets = get_legal_targets(firing_ship, all_ships, Broadside.R)
        assert len(targets) == 1
        assert targets[0].id == "test_target"

    def test_closest_target_rule_single_closest(self, firing_ship):
        """Test that only closest enemy is legal target."""
        # Two enemies at different ranges
        close_enemy = Ship(
            id="close",
            name="FS Close",
            side=Side.P2,
            bow_hex=HexCoord(col=7, row=5),  # 2 hexes away
            stern_hex=HexCoord(col=7, row=6),
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

        far_enemy = Ship(
            id="far",
            name="FS Far",
            side=Side.P2,
            bow_hex=HexCoord(col=10, row=5),  # 5 hexes away
            stern_hex=HexCoord(col=10, row=6),
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

        all_ships = {"firing": firing_ship, "close": close_enemy, "far": far_enemy}

        # Right broadside fires east
        targets = get_legal_targets(firing_ship, all_ships, Broadside.R)
        assert len(targets) == 1
        assert targets[0].id == "close"

    def test_tied_for_closest_both_legal(self, firing_ship):
        """Test that when two enemies are tied for closest, both are legal targets."""
        enemy1 = Ship(
            id="enemy1",
            name="FS Enemy 1",
            side=Side.P2,
            bow_hex=HexCoord(col=8, row=5),  # 3 hexes away
            stern_hex=HexCoord(col=8, row=6),
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

        enemy2 = Ship(
            id="enemy2",
            name="FS Enemy 2",
            side=Side.P2,
            bow_hex=HexCoord(col=8, row=7),  # Also 3 hexes away
            stern_hex=HexCoord(col=8, row=8),
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

        all_ships = {"firing": firing_ship, "enemy1": enemy1, "enemy2": enemy2}

        targets = get_legal_targets(firing_ship, all_ships, Broadside.R)
        assert len(targets) == 2
        target_ids = {t.id for t in targets}
        assert target_ids == {"enemy1", "enemy2"}

    def test_struck_ship_not_targetable(self, firing_ship):
        """Test that struck ships cannot be targeted."""
        # Both ships in right broadside arc (starboard/south for ship facing E)
        struck_enemy = Ship(
            id="struck",
            name="FS Struck",
            side=Side.P2,
            bow_hex=HexCoord(col=7, row=6),
            stern_hex=HexCoord(col=7, row=7),
            facing=Facing.W,
            battle_sail_speed=4,
            guns_L=10,
            guns_R=10,
            hull=0,
            rigging=10,
            crew=10,
            marines=2,
            load_L=LoadState.ROUNDSHOT,
            load_R=LoadState.ROUNDSHOT,
            struck=True,
        )

        unstruck_enemy = Ship(
            id="unstruck",
            name="FS Active",
            side=Side.P2,
            bow_hex=HexCoord(col=9, row=7),
            stern_hex=HexCoord(col=9, row=8),
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

        all_ships = {"firing": firing_ship, "struck": struck_enemy, "unstruck": unstruck_enemy}

        targets = get_legal_targets(firing_ship, all_ships, Broadside.R)
        # Should only target the unstruck ship, even though struck is closer
        assert len(targets) == 1
        assert targets[0].id == "unstruck"


class TestApplyDamage:
    """Test damage application to ships."""

    def test_apply_hull_damage(self, target_ship, hit_tables):
        """Test applying damage to hull."""
        # Create a mock hit result
        from wsim_core.engine.combat import HitResult

        hit_result = HitResult(
            hits=3,
            crew_casualties=1,
            gun_damage=0,
            range=3,
            range_bracket="medium",
            die_rolls=[4, 5, 6],
            modifiers_applied={},
        )

        initial_hull = target_ship.hull
        apply_damage(target_ship, hit_result, AimPoint.HULL, Broadside.R)

        assert target_ship.hull == initial_hull - 3
        assert target_ship.crew == 10 - 1
        assert target_ship.rigging == 10  # Unchanged

    def test_apply_rigging_damage(self, target_ship):
        """Test applying damage to rigging."""
        from wsim_core.engine.combat import HitResult

        hit_result = HitResult(
            hits=2,
            crew_casualties=0,
            gun_damage=0,
            range=3,
            range_bracket="medium",
            die_rolls=[5, 6],
            modifiers_applied={},
        )

        initial_rigging = target_ship.rigging
        apply_damage(target_ship, hit_result, AimPoint.RIGGING, Broadside.R)

        assert target_ship.rigging == initial_rigging - 2
        assert target_ship.hull == 12  # Unchanged
        assert target_ship.crew == 10  # No casualties for rigging hits

    def test_apply_gun_damage(self, target_ship):
        """Test applying gun damage at short range."""
        from wsim_core.engine.combat import HitResult

        hit_result = HitResult(
            hits=2,
            crew_casualties=1,
            gun_damage=2,
            range=1,
            range_bracket="short",
            die_rolls=[6, 6, 5, 6, 6],
            modifiers_applied={},
        )

        initial_guns = target_ship.guns_L + target_ship.guns_R
        apply_damage(target_ship, hit_result, AimPoint.HULL, Broadside.R)

        final_guns = target_ship.guns_L + target_ship.guns_R
        assert final_guns == initial_guns - 2

    def test_hull_zero_sets_struck(self, target_ship):
        """Test that hull reaching zero sets struck flag."""
        from wsim_core.engine.combat import HitResult

        # Deal enough damage to destroy hull
        hit_result = HitResult(
            hits=12,
            crew_casualties=0,
            gun_damage=0,
            range=1,
            range_bracket="short",
            die_rolls=[6] * 10,
            modifiers_applied={},
        )

        apply_damage(target_ship, hit_result, AimPoint.HULL, Broadside.R)

        assert target_ship.hull == 0
        assert target_ship.struck is True

    def test_damage_cannot_go_negative(self, target_ship):
        """Test that tracks cannot go negative."""
        from wsim_core.engine.combat import HitResult

        # Deal more damage than ship has hull
        hit_result = HitResult(
            hits=100,
            crew_casualties=50,
            gun_damage=50,
            range=1,
            range_bracket="short",
            die_rolls=[6] * 10,
            modifiers_applied={},
        )

        apply_damage(target_ship, hit_result, AimPoint.HULL, Broadside.R)

        assert target_ship.hull >= 0
        assert target_ship.crew >= 0
        assert target_ship.guns_L >= 0
        assert target_ship.guns_R >= 0
