"""Victory condition checking and game end detection."""

from wsim_core.models.common import GamePhase
from wsim_core.models.events import EventLogEntry
from wsim_core.models.game import Game


class VictoryResult:
    """Result of victory condition check."""

    def __init__(
        self,
        game_ended: bool,
        winner: str | None = None,
        reason: str | None = None,
        details: dict[str, int] | None = None,
    ):
        """Initialize victory result.

        Args:
            game_ended: Whether the game has ended
            winner: Winner side (P1, P2, or None for draw)
            reason: Human-readable reason for game end
            details: Optional additional details (e.g., scores)
        """
        self.game_ended = game_ended
        self.winner = winner
        self.reason = reason
        self.details = details or {}


def check_first_struck(game: Game) -> VictoryResult:
    """Check if any ship has struck.

    Victory condition: First ship to strike loses.

    Args:
        game: Current game state

    Returns:
        VictoryResult indicating if game ended and who won
    """
    struck_ships = [ship for ship in game.ships.values() if ship.struck]

    if not struck_ships:
        return VictoryResult(game_ended=False)

    # Find which side struck first
    struck_ship = struck_ships[0]
    winner = "P2" if struck_ship.side == "P1" else "P1"

    return VictoryResult(
        game_ended=True,
        winner=winner,
        reason=f"Ship {struck_ship.name} ({struck_ship.side}) has struck",
        details={"struck_ship_id": struck_ship.id, "struck_ship_name": struck_ship.name},
    )


def check_score_after_turns(game: Game) -> VictoryResult:
    """Check if turn limit reached and calculate scores.

    Victory condition: Compare remaining hull at turn limit.
    Winner is side with most total hull remaining.

    Args:
        game: Current game state

    Returns:
        VictoryResult indicating if game ended and who won
    """
    # Only check if turn limit is set and reached
    if game.turn_limit is None or game.turn_number < game.turn_limit:
        return VictoryResult(game_ended=False)

    # Calculate total remaining hull for each side
    p1_ships = game.get_ships_by_side("P1")
    p2_ships = game.get_ships_by_side("P2")

    p1_hull = sum(ship.hull for ship in p1_ships)
    p2_hull = sum(ship.hull for ship in p2_ships)

    # Determine winner
    if p1_hull > p2_hull:
        winner = "P1"
        reason = f"P1 wins on hull points: {p1_hull} vs {p2_hull}"
    elif p2_hull > p1_hull:
        winner = "P2"
        reason = f"P2 wins on hull points: {p2_hull} vs {p1_hull}"
    else:
        winner = None
        reason = f"Draw: both sides have {p1_hull} hull points"

    return VictoryResult(
        game_ended=True,
        winner=winner,
        reason=reason,
        details={"p1_hull": p1_hull, "p2_hull": p2_hull, "turn_limit": game.turn_limit},
    )


def check_first_side_struck_two_ships(game: Game) -> VictoryResult:
    """Check if one side has two ships struck.

    Victory condition: First side to lose two ships loses.

    Args:
        game: Current game state

    Returns:
        VictoryResult indicating if game ended and who won
    """
    # Count struck ships per side
    p1_ships = game.get_ships_by_side("P1")
    p2_ships = game.get_ships_by_side("P2")

    p1_struck_count = sum(1 for ship in p1_ships if ship.struck)
    p2_struck_count = sum(1 for ship in p2_ships if ship.struck)

    # Check if either side has lost two ships
    if p1_struck_count >= 2:
        struck_ships = [ship.name for ship in p1_ships if ship.struck]
        return VictoryResult(
            game_ended=True,
            winner="P2",
            reason=f"P1 has lost two ships: {', '.join(struck_ships[:2])}",
            details={"p1_struck": p1_struck_count, "p2_struck": p2_struck_count},
        )
    elif p2_struck_count >= 2:
        struck_ships = [ship.name for ship in p2_ships if ship.struck]
        return VictoryResult(
            game_ended=True,
            winner="P1",
            reason=f"P2 has lost two ships: {', '.join(struck_ships[:2])}",
            details={"p1_struck": p1_struck_count, "p2_struck": p2_struck_count},
        )

    return VictoryResult(game_ended=False)


def check_victory_condition(game: Game) -> VictoryResult:
    """Check if victory condition is met.

    Dispatches to appropriate victory condition checker based on game configuration.

    Args:
        game: Current game state

    Returns:
        VictoryResult indicating if game ended and who won

    Raises:
        ValueError: If victory condition type is unknown
    """
    victory_type = game.victory_condition

    if victory_type == "first_struck":
        return check_first_struck(game)
    elif victory_type == "score_after_turns":
        return check_score_after_turns(game)
    elif victory_type == "first_side_struck_two_ships":
        return check_first_side_struck_two_ships(game)
    else:
        raise ValueError(f"Unknown victory condition type: {victory_type}")


def create_victory_event(
    result: VictoryResult, turn_number: int, phase: GamePhase
) -> EventLogEntry:
    """Create an event log entry for game end.

    Args:
        result: Victory result with game end details
        turn_number: Current turn number
        phase: Current game phase

    Returns:
        Event log entry describing game end
    """
    return EventLogEntry(
        turn_number=turn_number,
        phase=phase,
        event_type="game_end",
        summary=result.reason or "Game ended",
        metadata={
            "winner": result.winner,
            "details": result.details,
        },
    )
