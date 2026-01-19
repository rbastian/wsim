"""Tests for ship model."""

import pytest
from pydantic import ValidationError

from wsim_core.models.common import Facing, LoadState, Side
from wsim_core.models.hex import HexCoord
from wsim_core.models.ship import Ship


def test_ship_creation_minimal() -> None:
    """Test ship creation with minimal required fields."""
    ship = Ship(
        id="test_ship_1",
        name="HMS Test",
        side=Side.P1,
        bow_hex=HexCoord(col=5, row=10),
        stern_hex=HexCoord(col=4, row=10),
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

    assert ship.id == "test_ship_1"
    assert ship.name == "HMS Test"
    assert ship.side == Side.P1
    assert ship.bow_hex == HexCoord(col=5, row=10)
    assert ship.stern_hex == HexCoord(col=4, row=10)
    assert ship.facing == Facing.E
    assert ship.battle_sail_speed == 4
    assert ship.guns_L == 10
    assert ship.guns_R == 10
    assert ship.carronades_L == 0  # Default
    assert ship.carronades_R == 0  # Default
    assert ship.hull == 12
    assert ship.rigging == 10
    assert ship.crew == 10
    assert ship.marines == 2
    assert ship.load_L == LoadState.ROUNDSHOT
    assert ship.load_R == LoadState.ROUNDSHOT
    assert ship.fouled is False  # Default
    assert ship.struck is False  # Default
    assert ship.turns_without_bow_advance == 0  # Default


def test_ship_with_carronades() -> None:
    """Test ship creation with carronades."""
    ship = Ship(
        id="test_ship_2",
        name="HMS Carronade",
        side=Side.P2,
        bow_hex=HexCoord(col=10, row=5),
        stern_hex=HexCoord(col=9, row=5),
        facing=Facing.W,
        battle_sail_speed=3,
        guns_L=8,
        guns_R=8,
        carronades_L=2,
        carronades_R=2,
        hull=10,
        rigging=9,
        crew=9,
        marines=1,
        load_L=LoadState.EMPTY,
        load_R=LoadState.ROUNDSHOT,
    )

    assert ship.carronades_L == 2
    assert ship.carronades_R == 2


def test_ship_validation_negative_stats() -> None:
    """Test ship validation rejects negative stats."""
    base_data = {
        "id": "test_ship",
        "name": "HMS Test",
        "side": Side.P1,
        "bow_hex": HexCoord(col=5, row=10),
        "stern_hex": HexCoord(col=4, row=10),
        "facing": Facing.E,
        "battle_sail_speed": 4,
        "guns_L": 10,
        "guns_R": 10,
        "hull": 12,
        "rigging": 10,
        "crew": 10,
        "marines": 2,
        "load_L": LoadState.ROUNDSHOT,
        "load_R": LoadState.ROUNDSHOT,
    }

    # Test negative hull
    with pytest.raises(ValidationError):
        Ship(**{**base_data, "hull": -1})

    # Test negative rigging
    with pytest.raises(ValidationError):
        Ship(**{**base_data, "rigging": -1})

    # Test negative crew
    with pytest.raises(ValidationError):
        Ship(**{**base_data, "crew": -1})

    # Test negative guns
    with pytest.raises(ValidationError):
        Ship(**{**base_data, "guns_L": -1})


def test_ship_validation_battle_sail_speed() -> None:
    """Test ship requires positive battle sail speed."""
    with pytest.raises(ValidationError):
        Ship(
            id="test_ship",
            name="HMS Test",
            side=Side.P1,
            bow_hex=HexCoord(col=5, row=10),
            stern_hex=HexCoord(col=4, row=10),
            facing=Facing.E,
            battle_sail_speed=0,  # Invalid
            guns_L=10,
            guns_R=10,
            hull=12,
            rigging=10,
            crew=10,
            marines=2,
            load_L=LoadState.ROUNDSHOT,
            load_R=LoadState.ROUNDSHOT,
        )


def test_ship_status_flags() -> None:
    """Test ship status flags."""
    ship = Ship(
        id="test_ship",
        name="HMS Test",
        side=Side.P1,
        bow_hex=HexCoord(col=5, row=10),
        stern_hex=HexCoord(col=4, row=10),
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
        fouled=True,
        struck=False,
    )

    assert ship.fouled is True
    assert ship.struck is False


def test_ship_drift_tracking() -> None:
    """Test ship tracks turns without bow advance."""
    ship = Ship(
        id="test_ship",
        name="HMS Test",
        side=Side.P1,
        bow_hex=HexCoord(col=5, row=10),
        stern_hex=HexCoord(col=4, row=10),
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
        turns_without_bow_advance=2,
    )

    assert ship.turns_without_bow_advance == 2
