"""Tests for game model."""

import pytest
from pydantic import ValidationError

from wsim_core.models.common import Facing, GamePhase, LoadState, Side, WindDirection
from wsim_core.models.events import EventLogEntry
from wsim_core.models.game import Game
from wsim_core.models.hex import HexCoord
from wsim_core.models.orders import ShipOrders, TurnOrders
from wsim_core.models.ship import Ship


def create_test_ship(ship_id: str, name: str, side: Side, bow_col: int, bow_row: int) -> Ship:
    """Helper to create a test ship."""
    return Ship(
        id=ship_id,
        name=name,
        side=side,
        bow_hex=HexCoord(col=bow_col, row=bow_row),
        stern_hex=HexCoord(col=bow_col - 1, row=bow_row),
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


def test_game_creation_minimal() -> None:
    """Test game creation with minimal fields."""
    ship1 = create_test_ship("ship_1", "HMS Test", Side.P1, 5, 10)
    ship2 = create_test_ship("ship_2", "FS Test", Side.P2, 15, 10)

    game = Game(
        id="game_1",
        scenario_id="test_scenario",
        map_width=25,
        map_height=20,
        wind_direction=WindDirection.W,
        ships={"ship_1": ship1, "ship_2": ship2},
    )

    assert game.id == "game_1"
    assert game.scenario_id == "test_scenario"
    assert game.turn_number == 1  # Default
    assert game.phase == GamePhase.PLANNING  # Default
    assert game.map_width == 25
    assert game.map_height == 20
    assert game.wind_direction == WindDirection.W
    assert len(game.ships) == 2
    assert game.p1_orders is None  # Default
    assert game.p2_orders is None  # Default
    assert len(game.event_log) == 0  # Default
    assert game.turn_limit is None  # Default
    assert game.victory_condition == "first_struck"  # Default


def test_game_with_orders() -> None:
    """Test game with player orders."""
    ship1 = create_test_ship("ship_1", "HMS Test", Side.P1, 5, 10)
    ship2 = create_test_ship("ship_2", "FS Test", Side.P2, 15, 10)

    p1_orders = TurnOrders(
        turn_number=1,
        side="P1",
        orders=[ShipOrders(ship_id="ship_1", movement_string="L1R1")],
        submitted=True,
    )

    game = Game(
        id="game_1",
        scenario_id="test_scenario",
        map_width=25,
        map_height=20,
        wind_direction=WindDirection.W,
        ships={"ship_1": ship1, "ship_2": ship2},
        p1_orders=p1_orders,
    )

    assert game.p1_orders is not None
    assert game.p1_orders.submitted is True
    assert game.p2_orders is None


def test_game_get_ship() -> None:
    """Test getting a ship by ID."""
    ship1 = create_test_ship("ship_1", "HMS Test", Side.P1, 5, 10)
    ship2 = create_test_ship("ship_2", "FS Test", Side.P2, 15, 10)

    game = Game(
        id="game_1",
        scenario_id="test_scenario",
        map_width=25,
        map_height=20,
        wind_direction=WindDirection.W,
        ships={"ship_1": ship1, "ship_2": ship2},
    )

    retrieved_ship = game.get_ship("ship_1")
    assert retrieved_ship.id == "ship_1"
    assert retrieved_ship.name == "HMS Test"

    # Test KeyError for non-existent ship
    with pytest.raises(KeyError):
        game.get_ship("non_existent")


def test_game_get_ships_by_side() -> None:
    """Test getting ships by side."""
    ship1 = create_test_ship("ship_1", "HMS Test 1", Side.P1, 5, 10)
    ship2 = create_test_ship("ship_2", "HMS Test 2", Side.P1, 6, 10)
    ship3 = create_test_ship("ship_3", "FS Test", Side.P2, 15, 10)

    game = Game(
        id="game_1",
        scenario_id="test_scenario",
        map_width=25,
        map_height=20,
        wind_direction=WindDirection.W,
        ships={"ship_1": ship1, "ship_2": ship2, "ship_3": ship3},
    )

    p1_ships = game.get_ships_by_side("P1")
    assert len(p1_ships) == 2
    assert all(ship.side == Side.P1 for ship in p1_ships)

    p2_ships = game.get_ships_by_side("P2")
    assert len(p2_ships) == 1
    assert p2_ships[0].side == Side.P2


def test_game_add_event() -> None:
    """Test adding events to game log."""
    ship1 = create_test_ship("ship_1", "HMS Test", Side.P1, 5, 10)

    game = Game(
        id="game_1",
        scenario_id="test_scenario",
        map_width=25,
        map_height=20,
        wind_direction=WindDirection.W,
        ships={"ship_1": ship1},
    )

    event = EventLogEntry(
        turn_number=1,
        phase=GamePhase.MOVEMENT,
        event_type="movement",
        summary="Ship moved",
    )

    game.add_event(event)

    assert len(game.event_log) == 1
    assert game.event_log[0].summary == "Ship moved"


def test_game_validation_positive_dimensions() -> None:
    """Test game requires positive map dimensions."""
    ship1 = create_test_ship("ship_1", "HMS Test", Side.P1, 5, 10)

    with pytest.raises(ValidationError):
        Game(
            id="game_1",
            scenario_id="test_scenario",
            map_width=0,  # Invalid
            map_height=20,
            wind_direction=WindDirection.W,
            ships={"ship_1": ship1},
        )

    with pytest.raises(ValidationError):
        Game(
            id="game_1",
            scenario_id="test_scenario",
            map_width=25,
            map_height=-1,  # Invalid
            wind_direction=WindDirection.W,
            ships={"ship_1": ship1},
        )


def test_game_with_turn_limit() -> None:
    """Test game with turn limit."""
    ship1 = create_test_ship("ship_1", "HMS Test", Side.P1, 5, 10)

    game = Game(
        id="game_1",
        scenario_id="test_scenario",
        map_width=25,
        map_height=20,
        wind_direction=WindDirection.W,
        ships={"ship_1": ship1},
        turn_limit=20,
    )

    assert game.turn_limit == 20


def test_game_validation_positive_turn_number() -> None:
    """Test game requires positive turn number."""
    ship1 = create_test_ship("ship_1", "HMS Test", Side.P1, 5, 10)

    with pytest.raises(ValidationError):
        Game(
            id="game_1",
            scenario_id="test_scenario",
            turn_number=0,  # Invalid
            map_width=25,
            map_height=20,
            wind_direction=WindDirection.W,
            ships={"ship_1": ship1},
        )
