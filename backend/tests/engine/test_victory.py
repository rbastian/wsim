"""Tests for victory condition checking."""

import pytest

from wsim_core.engine.victory import (
    VictoryResult,
    check_first_side_struck_two_ships,
    check_first_struck,
    check_score_after_turns,
    check_victory_condition,
    create_victory_event,
)
from wsim_core.models.common import Facing, GamePhase, LoadState, WindDirection
from wsim_core.models.game import Game
from wsim_core.models.hex import HexCoord
from wsim_core.models.ship import Ship


@pytest.fixture
def base_game():
    """Create a base game for testing."""
    ship1 = Ship(
        id="ship1",
        name="HMS Victory",
        side="P1",
        bow_hex=HexCoord(col=5, row=5),
        stern_hex=HexCoord(col=5, row=6),
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
    )

    ship2 = Ship(
        id="ship2",
        name="USS Constitution",
        side="P2",
        bow_hex=HexCoord(col=15, row=5),
        stern_hex=HexCoord(col=15, row=6),
        facing=Facing.S,
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

    game = Game(
        id="test-game",
        scenario_id="test_scenario",
        turn_number=1,
        phase=GamePhase.PLANNING,
        map_width=25,
        map_height=20,
        wind_direction=WindDirection.W,
        ships={"ship1": ship1, "ship2": ship2},
        turn_limit=20,
        victory_condition="first_struck",
    )

    return game


def test_victory_result_initialization():
    """Test VictoryResult initialization."""
    result = VictoryResult(game_ended=False)
    assert result.game_ended is False
    assert result.winner is None
    assert result.reason is None
    assert result.details == {}

    result_with_winner = VictoryResult(
        game_ended=True, winner="P1", reason="Test reason", details={"score": 100}
    )
    assert result_with_winner.game_ended is True
    assert result_with_winner.winner == "P1"
    assert result_with_winner.reason == "Test reason"
    assert result_with_winner.details == {"score": 100}


def test_check_first_struck_no_ships_struck(base_game):
    """Test check_first_struck when no ships struck."""
    result = check_first_struck(base_game)

    assert result.game_ended is False
    assert result.winner is None


def test_check_first_struck_p1_ship_struck(base_game):
    """Test check_first_struck when P1 ship strikes."""
    # Make P1 ship strike
    base_game.ships["ship1"].struck = True

    result = check_first_struck(base_game)

    assert result.game_ended is True
    assert result.winner == "P2"
    assert result.reason is not None
    assert "HMS Victory" in result.reason
    assert "P1" in result.reason
    assert "struck" in result.reason.lower()


def test_check_first_struck_p2_ship_struck(base_game):
    """Test check_first_struck when P2 ship strikes."""
    # Make P2 ship strike
    base_game.ships["ship2"].struck = True

    result = check_first_struck(base_game)

    assert result.game_ended is True
    assert result.winner == "P1"
    assert result.reason is not None
    assert "USS Constitution" in result.reason
    assert "P2" in result.reason
    assert "struck" in result.reason.lower()


def test_check_score_after_turns_not_reached(base_game):
    """Test check_score_after_turns when turn limit not reached."""
    base_game.turn_number = 10
    base_game.turn_limit = 20

    result = check_score_after_turns(base_game)

    assert result.game_ended is False


def test_check_score_after_turns_p1_wins(base_game):
    """Test check_score_after_turns at turn limit with P1 winning."""
    base_game.turn_number = 20
    base_game.turn_limit = 20
    # P1 has 12 hull, P2 has less
    base_game.ships["ship2"].hull = 8

    result = check_score_after_turns(base_game)

    assert result.game_ended is True
    assert result.winner == "P1"
    assert result.reason is not None
    assert "P1 wins on hull points" in result.reason
    assert "12 vs 8" in result.reason
    assert result.details["p1_hull"] == 12
    assert result.details["p2_hull"] == 8
    assert result.details["turn_limit"] == 20


def test_check_score_after_turns_p2_wins(base_game):
    """Test check_score_after_turns at turn limit with P2 winning."""
    base_game.turn_number = 20
    base_game.turn_limit = 20
    # P2 has more hull than P1
    base_game.ships["ship1"].hull = 6
    base_game.ships["ship2"].hull = 10

    result = check_score_after_turns(base_game)

    assert result.game_ended is True
    assert result.winner == "P2"
    assert result.reason is not None
    assert "P2 wins on hull points" in result.reason
    assert "10 vs 6" in result.reason
    assert result.details["p1_hull"] == 6
    assert result.details["p2_hull"] == 10


def test_check_score_after_turns_draw(base_game):
    """Test check_score_after_turns at turn limit with draw."""
    base_game.turn_number = 20
    base_game.turn_limit = 20
    # Equal hull
    base_game.ships["ship1"].hull = 8
    base_game.ships["ship2"].hull = 8

    result = check_score_after_turns(base_game)

    assert result.game_ended is True
    assert result.winner is None
    assert result.reason is not None
    assert "Draw" in result.reason
    assert "8 hull points" in result.reason


def test_check_score_after_turns_no_limit_set(base_game):
    """Test check_score_after_turns with no turn limit set."""
    base_game.turn_number = 50
    base_game.turn_limit = None

    result = check_score_after_turns(base_game)

    assert result.game_ended is False


def test_check_score_after_turns_multiple_ships_per_side(base_game):
    """Test check_score_after_turns with multiple ships per side."""
    # Add more ships
    ship3 = Ship(
        id="ship3",
        name="HMS Temeraire",
        side="P1",
        bow_hex=HexCoord(col=6, row=5),
        stern_hex=HexCoord(col=6, row=6),
        facing=Facing.N,
        battle_sail_speed=4,
        guns_L=10,
        guns_R=10,
        carronades_L=0,
        carronades_R=0,
        hull=10,
        rigging=10,
        crew=10,
        marines=2,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
    )

    ship4 = Ship(
        id="ship4",
        name="USS United States",
        side="P2",
        bow_hex=HexCoord(col=16, row=5),
        stern_hex=HexCoord(col=16, row=6),
        facing=Facing.S,
        battle_sail_speed=4,
        guns_L=10,
        guns_R=10,
        carronades_L=0,
        carronades_R=0,
        hull=8,
        rigging=10,
        crew=10,
        marines=2,
        load_L=LoadState.ROUNDSHOT,
        load_R=LoadState.ROUNDSHOT,
    )

    base_game.ships["ship3"] = ship3
    base_game.ships["ship4"] = ship4
    base_game.turn_number = 20
    base_game.turn_limit = 20

    # P1 total: 12 + 10 = 22, P2 total: 12 + 8 = 20
    result = check_score_after_turns(base_game)

    assert result.game_ended is True
    assert result.winner == "P1"
    assert result.details["p1_hull"] == 22
    assert result.details["p2_hull"] == 20


def test_check_first_side_struck_two_ships_no_strikes(base_game):
    """Test check_first_side_struck_two_ships when no ships struck."""
    result = check_first_side_struck_two_ships(base_game)

    assert result.game_ended is False


def test_check_first_side_struck_two_ships_one_strike(base_game):
    """Test check_first_side_struck_two_ships with only one ship struck."""
    base_game.ships["ship1"].struck = True

    result = check_first_side_struck_two_ships(base_game)

    assert result.game_ended is False


def test_check_first_side_struck_two_ships_p1_loses(base_game):
    """Test check_first_side_struck_two_ships when P1 loses two ships."""
    # Add more ships
    ship3 = Ship(
        id="ship3",
        name="HMS Temeraire",
        side="P1",
        bow_hex=HexCoord(col=6, row=5),
        stern_hex=HexCoord(col=6, row=6),
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
        struck=True,
    )

    base_game.ships["ship3"] = ship3
    base_game.ships["ship1"].struck = True

    result = check_first_side_struck_two_ships(base_game)

    assert result.game_ended is True
    assert result.winner == "P2"
    assert result.reason is not None
    assert "P1 has lost two ships" in result.reason
    assert result.details["p1_struck"] == 2
    assert result.details["p2_struck"] == 0


def test_check_first_side_struck_two_ships_p2_loses(base_game):
    """Test check_first_side_struck_two_ships when P2 loses two ships."""
    # Add more ships
    ship3 = Ship(
        id="ship3",
        name="USS United States",
        side="P2",
        bow_hex=HexCoord(col=16, row=5),
        stern_hex=HexCoord(col=16, row=6),
        facing=Facing.S,
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
        struck=True,
    )

    base_game.ships["ship3"] = ship3
    base_game.ships["ship2"].struck = True

    result = check_first_side_struck_two_ships(base_game)

    assert result.game_ended is True
    assert result.winner == "P1"
    assert result.reason is not None
    assert "P2 has lost two ships" in result.reason
    assert result.details["p1_struck"] == 0
    assert result.details["p2_struck"] == 2


def test_check_victory_condition_first_struck(base_game):
    """Test check_victory_condition dispatches to first_struck checker."""
    base_game.victory_condition = "first_struck"
    base_game.ships["ship1"].struck = True

    result = check_victory_condition(base_game)

    assert result.game_ended is True
    assert result.winner == "P2"


def test_check_victory_condition_score_after_turns(base_game):
    """Test check_victory_condition dispatches to score_after_turns checker."""
    base_game.victory_condition = "score_after_turns"
    base_game.turn_number = 20
    base_game.turn_limit = 20
    base_game.ships["ship1"].hull = 15
    base_game.ships["ship2"].hull = 8

    result = check_victory_condition(base_game)

    assert result.game_ended is True
    assert result.winner == "P1"


def test_check_victory_condition_first_side_struck_two_ships(base_game):
    """Test check_victory_condition dispatches to first_side_struck_two_ships checker."""
    base_game.victory_condition = "first_side_struck_two_ships"

    # Add another P1 ship
    ship3 = Ship(
        id="ship3",
        name="HMS Temeraire",
        side="P1",
        bow_hex=HexCoord(col=6, row=5),
        stern_hex=HexCoord(col=6, row=6),
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
        struck=True,
    )

    base_game.ships["ship3"] = ship3
    base_game.ships["ship1"].struck = True

    result = check_victory_condition(base_game)

    assert result.game_ended is True
    assert result.winner == "P2"


def test_check_victory_condition_unknown_type(base_game):
    """Test check_victory_condition with unknown victory type."""
    base_game.victory_condition = "unknown_type"

    with pytest.raises(ValueError) as exc_info:
        check_victory_condition(base_game)

    assert "Unknown victory condition type" in str(exc_info.value)
    assert "unknown_type" in str(exc_info.value)


def test_create_victory_event():
    """Test create_victory_event creates proper event log entry."""
    result = VictoryResult(
        game_ended=True,
        winner="P1",
        reason="P1 wins by hull points",
        details={"p1_hull": 20, "p2_hull": 10},
    )

    event = create_victory_event(result, turn_number=15, phase=GamePhase.COMBAT)

    assert event.turn_number == 15
    assert event.phase == GamePhase.COMBAT
    assert event.event_type == "game_end"
    assert event.summary == "P1 wins by hull points"
    assert event.metadata["winner"] == "P1"
    assert event.metadata["details"] == {"p1_hull": 20, "p2_hull": 10}


def test_create_victory_event_draw():
    """Test create_victory_event for a draw."""
    result = VictoryResult(game_ended=True, winner=None, reason="Game ended in a draw")

    event = create_victory_event(result, turn_number=20, phase=GamePhase.PLANNING)

    assert event.turn_number == 20
    assert event.phase == GamePhase.PLANNING
    assert event.event_type == "game_end"
    assert event.summary == "Game ended in a draw"
    assert event.metadata["winner"] is None


def test_multiple_victory_conditions_first_struck_takes_precedence(base_game):
    """Test that first_struck is checked and ends game immediately."""
    base_game.victory_condition = "first_struck"
    base_game.turn_number = 20
    base_game.turn_limit = 20
    base_game.ships["ship1"].struck = True
    base_game.ships["ship1"].hull = 0  # Even with no hull

    result = check_victory_condition(base_game)

    # Should end by first_struck, P2 wins
    assert result.game_ended is True
    assert result.winner == "P2"
    assert result.reason is not None
    assert "struck" in result.reason.lower()


def test_score_after_turns_exact_turn_limit(base_game):
    """Test score_after_turns triggers exactly at turn limit."""
    base_game.turn_number = 20
    base_game.turn_limit = 20

    result = check_score_after_turns(base_game)

    assert result.game_ended is True


def test_score_after_turns_just_before_limit(base_game):
    """Test score_after_turns doesn't trigger before turn limit."""
    base_game.turn_number = 19
    base_game.turn_limit = 20

    result = check_score_after_turns(base_game)

    assert result.game_ended is False


def test_check_first_side_struck_two_ships_more_than_two(base_game):
    """Test check_first_side_struck_two_ships when side has more than two ships struck."""
    # Add more ships to P1
    for i in range(3, 6):
        ship = Ship(
            id=f"ship{i}",
            name=f"Ship {i}",
            side="P1",
            bow_hex=HexCoord(col=i, row=5),
            stern_hex=HexCoord(col=i, row=6),
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
            struck=True,
        )
        base_game.ships[f"ship{i}"] = ship

    result = check_first_side_struck_two_ships(base_game)

    assert result.game_ended is True
    assert result.winner == "P2"
    assert result.details["p1_struck"] == 3


def test_victory_with_zero_hull_ships(base_game):
    """Test score victory calculation with zero hull ships."""
    base_game.victory_condition = "score_after_turns"
    base_game.turn_number = 20
    base_game.turn_limit = 20
    base_game.ships["ship1"].hull = 0
    base_game.ships["ship2"].hull = 5

    result = check_victory_condition(base_game)

    assert result.game_ended is True
    assert result.winner == "P2"
    assert result.details["p1_hull"] == 0
    assert result.details["p2_hull"] == 5
