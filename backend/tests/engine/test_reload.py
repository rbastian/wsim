"""Tests for broadside reload system."""

from wsim_core.engine.reload import (
    ReloadResult,
    can_reload_ship,
    create_reload_event,
    is_broadside_loaded,
    mark_broadside_fired,
    reload_all_ships,
    reload_broadside,
    reload_ship,
)
from wsim_core.models.common import Broadside, Facing, GamePhase, LoadState, Side
from wsim_core.models.hex import HexCoord
from wsim_core.models.ship import Ship


def create_test_ship(
    ship_id: str = "test_ship",
    load_l: LoadState = LoadState.ROUNDSHOT,
    load_r: LoadState = LoadState.ROUNDSHOT,
    struck: bool = False,
) -> Ship:
    """Create a test ship with specified load states."""
    return Ship(
        id=ship_id,
        name="Test Ship",
        side=Side.P1,
        bow_hex=HexCoord(col=5, row=5),
        stern_hex=HexCoord(col=5, row=6),
        facing=Facing.N,
        battle_sail_speed=4,
        guns_L=10,
        guns_R=10,
        hull=12,
        rigging=10,
        crew=10,
        marines=2,
        load_L=load_l,
        load_R=load_r,
        struck=struck,
    )


class TestMarkBroadsideFired:
    """Tests for mark_broadside_fired()."""

    def test_mark_left_broadside_fired(self):
        """Test marking left broadside as fired."""
        ship = create_test_ship()
        assert ship.load_L == LoadState.ROUNDSHOT

        mark_broadside_fired(ship, Broadside.L)

        assert ship.load_L == LoadState.EMPTY
        assert ship.load_R == LoadState.ROUNDSHOT  # Unchanged

    def test_mark_right_broadside_fired(self):
        """Test marking right broadside as fired."""
        ship = create_test_ship()
        assert ship.load_R == LoadState.ROUNDSHOT

        mark_broadside_fired(ship, Broadside.R)

        assert ship.load_L == LoadState.ROUNDSHOT  # Unchanged
        assert ship.load_R == LoadState.EMPTY

    def test_mark_already_empty_broadside(self):
        """Test marking an already empty broadside (idempotent)."""
        ship = create_test_ship(load_l=LoadState.EMPTY)

        mark_broadside_fired(ship, Broadside.L)

        assert ship.load_L == LoadState.EMPTY


class TestReloadBroadside:
    """Tests for reload_broadside()."""

    def test_reload_empty_left_broadside(self):
        """Test reloading an empty left broadside."""
        ship = create_test_ship(load_l=LoadState.EMPTY)

        result = reload_broadside(ship, Broadside.L)

        assert result is True
        assert ship.load_L == LoadState.ROUNDSHOT

    def test_reload_empty_right_broadside(self):
        """Test reloading an empty right broadside."""
        ship = create_test_ship(load_r=LoadState.EMPTY)

        result = reload_broadside(ship, Broadside.R)

        assert result is True
        assert ship.load_R == LoadState.ROUNDSHOT

    def test_reload_already_loaded_broadside(self):
        """Test that reloading an already loaded broadside does nothing."""
        ship = create_test_ship(load_l=LoadState.ROUNDSHOT)

        result = reload_broadside(ship, Broadside.L)

        assert result is False
        assert ship.load_L == LoadState.ROUNDSHOT


class TestReloadShip:
    """Tests for reload_ship()."""

    def test_reload_ship_with_both_empty(self):
        """Test reloading ship with both broadsides empty."""
        ship = create_test_ship(load_l=LoadState.EMPTY, load_r=LoadState.EMPTY)

        result = reload_ship(ship)

        assert isinstance(result, ReloadResult)
        assert result.ship_id == ship.id
        assert result.left_reloaded is True
        assert result.right_reloaded is True
        assert result.left_final_state == LoadState.ROUNDSHOT
        assert result.right_final_state == LoadState.ROUNDSHOT
        assert ship.load_L == LoadState.ROUNDSHOT
        assert ship.load_R == LoadState.ROUNDSHOT

    def test_reload_ship_with_left_empty_only(self):
        """Test reloading ship with only left broadside empty."""
        ship = create_test_ship(load_l=LoadState.EMPTY, load_r=LoadState.ROUNDSHOT)

        result = reload_ship(ship)

        assert result.left_reloaded is True
        assert result.right_reloaded is False
        assert result.left_final_state == LoadState.ROUNDSHOT
        assert result.right_final_state == LoadState.ROUNDSHOT

    def test_reload_ship_with_right_empty_only(self):
        """Test reloading ship with only right broadside empty."""
        ship = create_test_ship(load_l=LoadState.ROUNDSHOT, load_r=LoadState.EMPTY)

        result = reload_ship(ship)

        assert result.left_reloaded is False
        assert result.right_reloaded is True
        assert result.left_final_state == LoadState.ROUNDSHOT
        assert result.right_final_state == LoadState.ROUNDSHOT

    def test_reload_ship_with_both_loaded(self):
        """Test reloading ship with both broadsides already loaded."""
        ship = create_test_ship(load_l=LoadState.ROUNDSHOT, load_r=LoadState.ROUNDSHOT)

        result = reload_ship(ship)

        assert result.left_reloaded is False
        assert result.right_reloaded is False
        assert result.left_final_state == LoadState.ROUNDSHOT
        assert result.right_final_state == LoadState.ROUNDSHOT


class TestReloadAllShips:
    """Tests for reload_all_ships()."""

    def test_reload_multiple_ships(self):
        """Test reloading multiple ships at once."""
        ship1 = create_test_ship(ship_id="ship1", load_l=LoadState.EMPTY)
        ship2 = create_test_ship(ship_id="ship2", load_r=LoadState.EMPTY)
        ship3 = create_test_ship(ship_id="ship3", load_l=LoadState.ROUNDSHOT)

        results = reload_all_ships([ship1, ship2, ship3], turn_number=1)

        assert len(results) == 3
        assert results[0].ship_id == "ship1"
        assert results[0].left_reloaded is True
        assert results[1].ship_id == "ship2"
        assert results[1].right_reloaded is True
        assert results[2].ship_id == "ship3"
        assert results[2].left_reloaded is False

    def test_reload_skips_struck_ships(self):
        """Test that struck ships are not reloaded."""
        ship1 = create_test_ship(ship_id="ship1", load_l=LoadState.EMPTY, struck=False)
        ship2 = create_test_ship(ship_id="ship2", load_l=LoadState.EMPTY, struck=True)

        results = reload_all_ships([ship1, ship2], turn_number=1)

        # Only ship1 should be in results (ship2 is struck)
        assert len(results) == 1
        assert results[0].ship_id == "ship1"
        assert ship1.load_L == LoadState.ROUNDSHOT
        # ship2 should remain empty since it was struck
        assert ship2.load_L == LoadState.EMPTY

    def test_reload_empty_list(self):
        """Test reloading with empty ship list."""
        results = reload_all_ships([], turn_number=1)
        assert results == []


class TestIsBroadsideLoaded:
    """Tests for is_broadside_loaded()."""

    def test_loaded_left_broadside(self):
        """Test checking a loaded left broadside."""
        ship = create_test_ship(load_l=LoadState.ROUNDSHOT)
        assert is_broadside_loaded(ship, Broadside.L) is True

    def test_empty_left_broadside(self):
        """Test checking an empty left broadside."""
        ship = create_test_ship(load_l=LoadState.EMPTY)
        assert is_broadside_loaded(ship, Broadside.L) is False

    def test_loaded_right_broadside(self):
        """Test checking a loaded right broadside."""
        ship = create_test_ship(load_r=LoadState.ROUNDSHOT)
        assert is_broadside_loaded(ship, Broadside.R) is True

    def test_empty_right_broadside(self):
        """Test checking an empty right broadside."""
        ship = create_test_ship(load_r=LoadState.EMPTY)
        assert is_broadside_loaded(ship, Broadside.R) is False


class TestCanReloadShip:
    """Tests for can_reload_ship()."""

    def test_can_reload_with_empty_left(self):
        """Test ship can reload when left broadside is empty."""
        ship = create_test_ship(load_l=LoadState.EMPTY)
        assert can_reload_ship(ship) is True

    def test_can_reload_with_empty_right(self):
        """Test ship can reload when right broadside is empty."""
        ship = create_test_ship(load_r=LoadState.EMPTY)
        assert can_reload_ship(ship) is True

    def test_can_reload_with_both_empty(self):
        """Test ship can reload when both broadsides empty."""
        ship = create_test_ship(load_l=LoadState.EMPTY, load_r=LoadState.EMPTY)
        assert can_reload_ship(ship) is True

    def test_cannot_reload_with_both_loaded(self):
        """Test ship cannot reload when both broadsides loaded."""
        ship = create_test_ship(load_l=LoadState.ROUNDSHOT, load_r=LoadState.ROUNDSHOT)
        assert can_reload_ship(ship) is False

    def test_cannot_reload_struck_ship(self):
        """Test struck ship cannot reload even with empty broadsides."""
        ship = create_test_ship(load_l=LoadState.EMPTY, struck=True)
        assert can_reload_ship(ship) is False


class TestCreateReloadEvent:
    """Tests for create_reload_event()."""

    def test_event_for_both_reloaded(self):
        """Test event creation when both broadsides reloaded."""
        result = ReloadResult(
            ship_id="test_ship",
            left_reloaded=True,
            right_reloaded=True,
            left_final_state=LoadState.ROUNDSHOT,
            right_final_state=LoadState.ROUNDSHOT,
        )

        event = create_reload_event(result, turn_number=3, ship_name="HMS Victory")

        assert event.turn_number == 3
        assert event.phase == GamePhase.RELOAD
        assert event.event_type == "reload"
        assert "HMS Victory" in event.summary
        assert "L" in event.summary
        assert "R" in event.summary
        assert event.metadata["ship_id"] == "test_ship"
        assert event.metadata["left_reloaded"] is True
        assert event.metadata["right_reloaded"] is True

    def test_event_for_left_only_reloaded(self):
        """Test event creation when only left broadside reloaded."""
        result = ReloadResult(
            ship_id="test_ship",
            left_reloaded=True,
            right_reloaded=False,
            left_final_state=LoadState.ROUNDSHOT,
            right_final_state=LoadState.ROUNDSHOT,
        )

        event = create_reload_event(result, turn_number=2, ship_name="FS Vengeur")

        assert "FS Vengeur" in event.summary
        assert "L" in event.summary
        assert "R" not in event.summary or "L, R" not in event.summary

    def test_event_for_no_reloading_needed(self):
        """Test event creation when no reloading was needed."""
        result = ReloadResult(
            ship_id="test_ship",
            left_reloaded=False,
            right_reloaded=False,
            left_final_state=LoadState.ROUNDSHOT,
            right_final_state=LoadState.ROUNDSHOT,
        )

        event = create_reload_event(result, turn_number=1, ship_name="HMS Swift")

        assert "HMS Swift" in event.summary
        assert "No reloading needed" in event.summary
        assert event.metadata["left_reloaded"] is False
        assert event.metadata["right_reloaded"] is False


class TestLoadStateTransitions:
    """Integration tests for complete load state transitions."""

    def test_fire_and_reload_cycle(self):
        """Test complete cycle: loaded -> fire -> empty -> reload -> loaded."""
        ship = create_test_ship()

        # Initial state: loaded
        assert ship.load_L == LoadState.ROUNDSHOT
        assert is_broadside_loaded(ship, Broadside.L) is True

        # Fire broadside
        mark_broadside_fired(ship, Broadside.L)
        assert ship.load_L == LoadState.EMPTY
        assert is_broadside_loaded(ship, Broadside.L) is False

        # Reload
        result = reload_ship(ship)
        assert result.left_reloaded is True
        assert ship.load_L == LoadState.ROUNDSHOT
        assert is_broadside_loaded(ship, Broadside.L) is True

    def test_fire_both_broadsides_reload_both(self):
        """Test firing both broadsides and reloading both."""
        ship = create_test_ship()

        # Fire both broadsides
        mark_broadside_fired(ship, Broadside.L)
        mark_broadside_fired(ship, Broadside.R)

        assert ship.load_L == LoadState.EMPTY
        assert ship.load_R == LoadState.EMPTY

        # Reload both
        result = reload_ship(ship)

        assert result.left_reloaded is True
        assert result.right_reloaded is True
        assert ship.load_L == LoadState.ROUNDSHOT
        assert ship.load_R == LoadState.ROUNDSHOT

    def test_multiple_turns_of_combat(self):
        """Test multiple turns of firing and reloading."""
        ship = create_test_ship()

        for _turn in range(3):
            # Fire left broadside
            mark_broadside_fired(ship, Broadside.L)
            assert ship.load_L == LoadState.EMPTY

            # Reload
            result = reload_ship(ship)
            assert result.left_reloaded is True
            assert ship.load_L == LoadState.ROUNDSHOT
