"""Tests for hex coordinate model."""

import pytest
from pydantic import ValidationError

from wsim_core.models.hex import HexCoord


def test_hex_coord_creation() -> None:
    """Test basic HexCoord creation."""
    coord = HexCoord(col=5, row=10)
    assert coord.col == 5
    assert coord.row == 10


def test_hex_coord_validation_positive() -> None:
    """Test HexCoord requires non-negative coordinates."""
    # Valid coords
    HexCoord(col=0, row=0)  # Origin is valid

    # Invalid coords
    with pytest.raises(ValidationError):
        HexCoord(col=-1, row=5)

    with pytest.raises(ValidationError):
        HexCoord(col=5, row=-1)


def test_hex_coord_equality() -> None:
    """Test HexCoord equality comparison."""
    coord1 = HexCoord(col=5, row=10)
    coord2 = HexCoord(col=5, row=10)
    coord3 = HexCoord(col=6, row=10)

    assert coord1 == coord2
    assert coord1 != coord3


def test_hex_coord_equality_with_non_hex() -> None:
    """Test HexCoord equality with non-HexCoord object."""
    coord = HexCoord(col=5, row=10)
    # Should return NotImplemented when comparing with non-HexCoord
    assert coord != "not a coord"
    assert coord != (5, 10)
    assert coord != 42


def test_hex_coord_hash() -> None:
    """Test HexCoord can be used as dict key."""
    coord1 = HexCoord(col=5, row=10)
    coord2 = HexCoord(col=5, row=10)
    coord3 = HexCoord(col=6, row=10)

    # Should work as dict keys
    coord_dict = {coord1: "value1"}
    coord_dict[coord2] = "value2"  # Should overwrite
    coord_dict[coord3] = "value3"

    assert len(coord_dict) == 2
    assert coord_dict[coord1] == "value2"
    assert coord_dict[coord3] == "value3"


def test_hex_coord_repr() -> None:
    """Test HexCoord string representation."""
    coord = HexCoord(col=5, row=10)
    assert repr(coord) == "HexCoord(5, 10)"
