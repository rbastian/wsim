"""Tests for combat resolution and hit tables."""

import pytest

from wsim_core.engine.combat import (
    HitTables,
    can_fire_broadside,
    get_crew_quality_modifier,
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
