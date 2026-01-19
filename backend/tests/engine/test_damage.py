"""Tests for damage application system."""

import pytest

from wsim_core.engine.combat import HitResult
from wsim_core.engine.damage import (
    apply_hit_result_to_ship,
    create_damage_event,
)
from wsim_core.models.common import AimPoint, Broadside, Facing, LoadState, Side
from wsim_core.models.hex import HexCoord
from wsim_core.models.ship import Ship


@pytest.fixture
def test_ship() -> Ship:
    """Create a test ship with standard stats."""
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
        carronades_L=0,
        carronades_R=0,
        hull=12,
        rigging=10,
        crew=10,
        marines=2,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
        fouled=False,
        struck=False,
    )


@pytest.fixture
def damaged_ship() -> Ship:
    """Create a ship with reduced stats."""
    return Ship(
        id="damaged_ship",
        name="HMS Damaged",
        side=Side.P1,
        bow_hex=HexCoord(col=10, row=10),
        stern_hex=HexCoord(col=10, row=11),
        facing=Facing.N,
        battle_sail_speed=4,
        guns_L=3,
        guns_R=5,
        carronades_L=0,
        carronades_R=0,
        hull=4,
        rigging=3,
        crew=5,
        marines=1,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
        fouled=False,
        struck=False,
    )


class TestHullDamage:
    """Test applying hull damage."""

    def test_basic_hull_damage(self, test_ship: Ship) -> None:
        """Test basic hull damage application."""
        hit_result = HitResult(
            hits=5,
            crew_casualties=0,
            gun_damage=0,
            range=3,
            range_bracket="medium",
            die_rolls=[4, 5, 6, 4, 5],
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(test_ship, hit_result, AimPoint.HULL)

        assert damage.hull_damage == 5
        assert test_ship.hull == 7  # 12 - 5
        assert damage.previous_hull == 12
        assert not damage.struck

    def test_hull_damage_cannot_go_negative(self, test_ship: Ship) -> None:
        """Test that hull cannot go below 0."""
        hit_result = HitResult(
            hits=20,  # More than ship has
            crew_casualties=0,
            gun_damage=0,
            range=3,
            range_bracket="medium",
            die_rolls=[6] * 10,
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(test_ship, hit_result, AimPoint.HULL)

        assert damage.hull_damage == 12  # Only had 12 hull
        assert test_ship.hull == 0
        assert damage.struck  # Ship struck when hull reaches 0

    def test_hull_reduced_to_zero_causes_struck(self, damaged_ship: Ship) -> None:
        """Test that reducing hull to 0 causes ship to strike."""
        hit_result = HitResult(
            hits=4,  # Exactly enough to sink
            crew_casualties=0,
            gun_damage=0,
            range=2,
            range_bracket="short",
            die_rolls=[6, 6, 5, 5],
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(damaged_ship, hit_result, AimPoint.HULL)

        assert damaged_ship.hull == 0
        assert damage.struck
        assert damaged_ship.struck


class TestCrewCasualties:
    """Test crew and marine casualties."""

    def test_casualties_hit_marines_first(self, test_ship: Ship) -> None:
        """Test that casualties are taken from marines first."""
        hit_result = HitResult(
            hits=5,
            crew_casualties=2,  # Should take both marines
            gun_damage=0,
            range=2,
            range_bracket="short",
            die_rolls=[5, 6],
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(test_ship, hit_result, AimPoint.HULL)

        assert damage.marines_lost == 2
        assert damage.crew_lost == 0
        assert test_ship.marines == 0
        assert test_ship.crew == 10  # Unchanged

    def test_casualties_overflow_to_crew(self, test_ship: Ship) -> None:
        """Test that casualties overflow from marines to crew."""
        hit_result = HitResult(
            hits=5,
            crew_casualties=5,  # 2 marines + 3 crew
            gun_damage=0,
            range=2,
            range_bracket="short",
            die_rolls=[5, 6, 4, 5, 6],
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(test_ship, hit_result, AimPoint.HULL)

        assert damage.marines_lost == 2
        assert damage.crew_lost == 3
        assert test_ship.marines == 0
        assert test_ship.crew == 7

    def test_casualties_cannot_go_negative(self, test_ship: Ship) -> None:
        """Test that crew/marines cannot go below 0."""
        hit_result = HitResult(
            hits=5,
            crew_casualties=50,  # Way more than available
            gun_damage=0,
            range=2,
            range_bracket="short",
            die_rolls=[6] * 10,
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(test_ship, hit_result, AimPoint.HULL)

        assert damage.marines_lost == 2
        assert damage.crew_lost == 10
        assert test_ship.marines == 0
        assert test_ship.crew == 0
        assert damage.struck  # All crew lost

    def test_all_crew_lost_causes_struck(self, damaged_ship: Ship) -> None:
        """Test that losing all crew causes ship to strike."""
        # damaged_ship has 5 crew + 1 marine = 6 total
        hit_result = HitResult(
            hits=4,
            crew_casualties=6,  # Exactly enough
            gun_damage=0,
            range=2,
            range_bracket="short",
            die_rolls=[6] * 6,
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(damaged_ship, hit_result, AimPoint.HULL)

        assert damaged_ship.crew == 0
        assert damaged_ship.marines == 0
        assert damage.struck
        assert damaged_ship.struck


class TestGunDamage:
    """Test gun damage distribution."""

    def test_gun_damage_to_left_broadside(self, test_ship: Ship) -> None:
        """Test gun damage to specific broadside."""
        hit_result = HitResult(
            hits=5,
            crew_casualties=0,
            gun_damage=3,
            range=2,
            range_bracket="short",
            die_rolls=[5, 6, 4],
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(test_ship, hit_result, AimPoint.HULL, Broadside.L)

        assert damage.guns_lost_L == 3
        assert damage.guns_lost_R == 0
        assert test_ship.guns_L == 7
        assert test_ship.guns_R == 10

    def test_gun_damage_to_right_broadside(self, test_ship: Ship) -> None:
        """Test gun damage to right broadside."""
        hit_result = HitResult(
            hits=5,
            crew_casualties=0,
            gun_damage=4,
            range=2,
            range_bracket="short",
            die_rolls=[5, 6, 4, 5],
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(test_ship, hit_result, AimPoint.HULL, Broadside.R)

        assert damage.guns_lost_L == 0
        assert damage.guns_lost_R == 4
        assert test_ship.guns_L == 10
        assert test_ship.guns_R == 6

    def test_gun_damage_distributed_evenly_when_no_target_broadside(self, test_ship: Ship) -> None:
        """Test gun damage distributes evenly when no specific broadside targeted."""
        hit_result = HitResult(
            hits=5,
            crew_casualties=0,
            gun_damage=6,  # Should be 3 per side
            range=2,
            range_bracket="short",
            die_rolls=[5, 6, 4, 5, 6, 4],
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(test_ship, hit_result, AimPoint.HULL, None)

        assert damage.guns_lost_L == 3
        assert damage.guns_lost_R == 3
        assert test_ship.guns_L == 7
        assert test_ship.guns_R == 7

    def test_gun_damage_odd_number_distributed(self, test_ship: Ship) -> None:
        """Test odd gun damage distributes correctly (left gets extra)."""
        hit_result = HitResult(
            hits=5,
            crew_casualties=0,
            gun_damage=5,  # Odd number
            range=2,
            range_bracket="short",
            die_rolls=[5, 6, 4, 5, 6],
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(test_ship, hit_result, AimPoint.HULL, None)

        assert damage.guns_lost_L == 3  # Left gets extra
        assert damage.guns_lost_R == 2
        assert test_ship.guns_L == 7
        assert test_ship.guns_R == 8

    def test_gun_damage_cannot_exceed_available(self, damaged_ship: Ship) -> None:
        """Test that gun damage cannot exceed guns available."""
        # damaged_ship has 3L and 5R = 8 total
        hit_result = HitResult(
            hits=5,
            crew_casualties=0,
            gun_damage=20,  # Way more than available
            range=2,
            range_bracket="short",
            die_rolls=[6] * 10,
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(damaged_ship, hit_result, AimPoint.HULL, Broadside.L)

        assert damage.guns_lost_L == 3  # Only had 3
        assert damage.guns_lost_R == 0
        assert damaged_ship.guns_L == 0
        assert damaged_ship.guns_R == 5


class TestRiggingDamage:
    """Test rigging damage."""

    def test_basic_rigging_damage(self, test_ship: Ship) -> None:
        """Test basic rigging damage application."""
        hit_result = HitResult(
            hits=4,
            crew_casualties=0,  # Should be ignored for rigging
            gun_damage=0,
            range=3,
            range_bracket="medium",
            die_rolls=[4, 5, 6, 4],
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(test_ship, hit_result, AimPoint.RIGGING)

        assert damage.rigging_damage == 4
        assert test_ship.rigging == 6  # 10 - 4
        assert damage.hull_damage == 0
        assert damage.crew_lost == 0
        assert damage.marines_lost == 0
        assert damage.guns_lost_L == 0
        assert damage.guns_lost_R == 0

    def test_rigging_damage_cannot_go_negative(self, test_ship: Ship) -> None:
        """Test that rigging cannot go below 0."""
        hit_result = HitResult(
            hits=20,  # More than ship has
            crew_casualties=0,
            gun_damage=0,
            range=3,
            range_bracket="medium",
            die_rolls=[6] * 10,
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(test_ship, hit_result, AimPoint.RIGGING)

        assert damage.rigging_damage == 10  # Only had 10 rigging
        assert test_ship.rigging == 0
        assert not damage.struck  # Rigging damage doesn't cause struck

    def test_rigging_damage_ignores_crew_casualties(self, test_ship: Ship) -> None:
        """Test that crew casualties are ignored when aiming at rigging."""
        hit_result = HitResult(
            hits=4,
            crew_casualties=5,  # Should be ignored
            gun_damage=3,  # Should be ignored
            range=3,
            range_bracket="medium",
            die_rolls=[4, 5, 6, 4],
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(test_ship, hit_result, AimPoint.RIGGING)

        assert damage.rigging_damage == 4
        assert damage.crew_lost == 0
        assert damage.marines_lost == 0
        assert damage.guns_lost_L == 0
        assert damage.guns_lost_R == 0
        assert test_ship.crew == 10  # Unchanged
        assert test_ship.marines == 2  # Unchanged
        assert test_ship.guns_L == 10  # Unchanged


class TestDamageEvent:
    """Test damage event creation."""

    def test_create_hull_damage_event(self, test_ship: Ship) -> None:
        """Test creating event for hull damage."""
        hit_result = HitResult(
            hits=5,
            crew_casualties=3,
            gun_damage=2,
            range=2,
            range_bracket="short",
            die_rolls=[5, 6, 4, 5, 6],
            modifiers_applied={"crew_quality": -1},
        )

        damage = apply_hit_result_to_ship(test_ship, hit_result, AimPoint.HULL, Broadside.L)
        event = create_damage_event(
            firing_ship_id="attacker_1",
            target_ship_id=test_ship.id,
            broadside=Broadside.L,
            aim=AimPoint.HULL,
            hit_result=hit_result,
            damage=damage,
            turn_number=3,
        )

        assert event.turn_number == 3
        assert event.event_type == "damage"
        assert "attacker_1" in event.summary
        assert test_ship.id in event.summary
        assert "hull" in event.summary
        assert event.modifiers == {"crew_quality": -1}
        assert event.state_diff["target_ship_id"] == test_ship.id
        assert event.state_diff["hull"]["before"] == 12
        assert event.state_diff["hull"]["after"] == 7

    def test_create_rigging_damage_event(self, test_ship: Ship) -> None:
        """Test creating event for rigging damage."""
        hit_result = HitResult(
            hits=4,
            crew_casualties=0,
            gun_damage=0,
            range=5,
            range_bracket="medium",
            die_rolls=[4, 5, 6, 4],
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(test_ship, hit_result, AimPoint.RIGGING)
        event = create_damage_event(
            firing_ship_id="attacker_2",
            target_ship_id=test_ship.id,
            broadside=Broadside.R,
            aim=AimPoint.RIGGING,
            hit_result=hit_result,
            damage=damage,
            turn_number=5,
        )

        assert event.turn_number == 5
        assert "rigging" in event.summary
        assert event.state_diff["rigging"]["before"] == 10
        assert event.state_diff["rigging"]["after"] == 6

    def test_create_struck_event(self, damaged_ship: Ship) -> None:
        """Test event creation when ship strikes."""
        hit_result = HitResult(
            hits=10,  # Enough to sink
            crew_casualties=0,
            gun_damage=0,
            range=1,
            range_bracket="short",
            die_rolls=[6] * 5,
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(damaged_ship, hit_result, AimPoint.HULL)
        event = create_damage_event(
            firing_ship_id="killer",
            target_ship_id=damaged_ship.id,
            broadside=Broadside.L,
            aim=AimPoint.HULL,
            hit_result=hit_result,
            damage=damage,
            turn_number=7,
        )

        assert "STRUCK" in event.summary
        assert event.state_diff["struck"] is True

    def test_create_miss_event(self, test_ship: Ship) -> None:
        """Test event creation when no hits occurred."""
        hit_result = HitResult(
            hits=0,
            crew_casualties=0,
            gun_damage=0,
            range=6,
            range_bracket="long",
            die_rolls=[1, 2, 1],
            modifiers_applied={"crew_quality": -2},
        )

        damage = apply_hit_result_to_ship(test_ship, hit_result, AimPoint.HULL)
        event = create_damage_event(
            firing_ship_id="miss_ship",
            target_ship_id=test_ship.id,
            broadside=Broadside.R,
            aim=AimPoint.HULL,
            hit_result=hit_result,
            damage=damage,
            turn_number=2,
        )

        assert "No hits" in event.summary
        assert event.state_diff["hull"]["before"] == event.state_diff["hull"]["after"]


class TestComplexScenarios:
    """Test complex damage scenarios."""

    def test_massive_damage_all_systems(self, test_ship: Ship) -> None:
        """Test applying massive damage across all systems."""
        hit_result = HitResult(
            hits=15,  # More than hull
            crew_casualties=20,  # More than crew+marines
            gun_damage=25,  # More than guns
            range=1,
            range_bracket="short",
            die_rolls=[6] * 20,
            modifiers_applied={},
        )

        damage = apply_hit_result_to_ship(test_ship, hit_result, AimPoint.HULL)

        # Everything should be at 0
        assert test_ship.hull == 0
        assert test_ship.crew == 0
        assert test_ship.marines == 0
        assert test_ship.guns_L == 0
        assert test_ship.guns_R == 0
        assert damage.struck
        assert test_ship.struck

    def test_sequential_damage_applications(self, test_ship: Ship) -> None:
        """Test applying damage multiple times."""
        # First hit
        hit_result_1 = HitResult(
            hits=3,
            crew_casualties=2,
            gun_damage=0,
            range=3,
            range_bracket="medium",
            die_rolls=[4, 5, 6],
            modifiers_applied={},
        )
        _damage_1 = apply_hit_result_to_ship(test_ship, hit_result_1, AimPoint.HULL)
        assert test_ship.hull == 9
        assert test_ship.marines == 0  # 2 marines lost

        # Second hit
        hit_result_2 = HitResult(
            hits=4,
            crew_casualties=3,
            gun_damage=2,
            range=2,
            range_bracket="short",
            die_rolls=[5, 6, 5, 6],
            modifiers_applied={},
        )
        _damage_2 = apply_hit_result_to_ship(test_ship, hit_result_2, AimPoint.HULL, Broadside.R)
        assert test_ship.hull == 5  # 9 - 4
        assert test_ship.crew == 7  # 10 - 3 (marines already gone)
        assert test_ship.guns_R == 8  # 10 - 2

        # Not struck yet
        assert not test_ship.struck
