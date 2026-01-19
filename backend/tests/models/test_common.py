"""Tests for common types and enums."""

from wsim_core.models.common import (
    AimPoint,
    Broadside,
    Facing,
    GamePhase,
    LoadState,
    Side,
    WindDirection,
)


def test_side_enum() -> None:
    """Test Side enum values."""
    assert Side.P1 == "P1"
    assert Side.P2 == "P2"
    assert len(list(Side)) == 2


def test_facing_enum() -> None:
    """Test Facing enum values."""
    assert Facing.N == "N"
    assert Facing.NE == "NE"
    assert Facing.E == "E"
    assert Facing.SE == "SE"
    assert Facing.S == "S"
    assert Facing.SW == "SW"
    assert Facing.W == "W"
    assert Facing.NW == "NW"
    assert len(list(Facing)) == 8


def test_wind_direction_enum() -> None:
    """Test WindDirection enum values."""
    assert WindDirection.N == "N"
    assert WindDirection.NE == "NE"
    assert WindDirection.E == "E"
    assert WindDirection.SE == "SE"
    assert WindDirection.S == "S"
    assert WindDirection.SW == "SW"
    assert WindDirection.W == "W"
    assert WindDirection.NW == "NW"
    assert len(list(WindDirection)) == 8


def test_load_state_enum() -> None:
    """Test LoadState enum values."""
    assert LoadState.EMPTY == "E"
    assert LoadState.ROUNDSHOT == "R"
    assert len(list(LoadState)) == 2


def test_game_phase_enum() -> None:
    """Test GamePhase enum values."""
    assert GamePhase.PLANNING == "planning"
    assert GamePhase.MOVEMENT == "movement"
    assert GamePhase.COMBAT == "combat"
    assert GamePhase.RELOAD == "reload"
    assert len(list(GamePhase)) == 4


def test_broadside_enum() -> None:
    """Test Broadside enum values."""
    assert Broadside.L == "L"
    assert Broadside.R == "R"
    assert len(list(Broadside)) == 2


def test_aim_point_enum() -> None:
    """Test AimPoint enum values."""
    assert AimPoint.HULL == "hull"
    assert AimPoint.RIGGING == "rigging"
    assert len(list(AimPoint)) == 2
