"""Tests for orders models."""

import pytest
from pydantic import ValidationError

from wsim_core.models.orders import ShipOrders, TurnOrders


def test_ship_orders_creation() -> None:
    """Test basic ship orders creation."""
    orders = ShipOrders(ship_id="ship_1", movement_string="L1R1")

    assert orders.ship_id == "ship_1"
    assert orders.movement_string == "L1R1"


def test_ship_orders_validation_patterns() -> None:
    """Test ship orders validates movement string patterns."""
    # Valid patterns
    ShipOrders(ship_id="ship_1", movement_string="0")
    ShipOrders(ship_id="ship_1", movement_string="L1R1")
    ShipOrders(ship_id="ship_1", movement_string="LLR2")
    ShipOrders(ship_id="ship_1", movement_string="R")
    ShipOrders(ship_id="ship_1", movement_string="1")

    # Invalid patterns should fail validation
    with pytest.raises(ValidationError):
        ShipOrders(ship_id="ship_1", movement_string="X")  # Invalid character

    with pytest.raises(ValidationError):
        ShipOrders(ship_id="ship_1", movement_string="L1R1X")  # Invalid character

    with pytest.raises(ValidationError):
        ShipOrders(ship_id="ship_1", movement_string="l1r1")  # Lowercase


def test_turn_orders_creation() -> None:
    """Test turn orders creation."""
    orders = TurnOrders(
        turn_number=1,
        side="P1",
        orders=[
            ShipOrders(ship_id="ship_1", movement_string="L1R1"),
            ShipOrders(ship_id="ship_2", movement_string="0"),
        ],
    )

    assert orders.turn_number == 1
    assert orders.side == "P1"
    assert len(orders.orders) == 2
    assert orders.submitted is False  # Default


def test_turn_orders_submitted_flag() -> None:
    """Test turn orders submitted flag."""
    orders = TurnOrders(
        turn_number=1,
        side="P2",
        orders=[ShipOrders(ship_id="ship_1", movement_string="R2")],
        submitted=True,
    )

    assert orders.submitted is True


def test_turn_orders_validation_turn_number() -> None:
    """Test turn orders requires positive turn number."""
    with pytest.raises(ValidationError):
        TurnOrders(
            turn_number=0,  # Invalid
            side="P1",
            orders=[],
        )

    with pytest.raises(ValidationError):
        TurnOrders(
            turn_number=-1,  # Invalid
            side="P1",
            orders=[],
        )


def test_turn_orders_empty_orders_list() -> None:
    """Test turn orders can have empty orders list."""
    orders = TurnOrders(turn_number=1, side="P1", orders=[])

    assert len(orders.orders) == 0
