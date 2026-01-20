"""Game state model."""

from pydantic import BaseModel, Field

from .common import GamePhase, WindDirection
from .events import EventLogEntry
from .orders import TurnOrders
from .ship import Ship


class Game(BaseModel):
    """Complete game state.

    Represents the entire state of a game including ships, wind, phase, and history.
    """

    # Identity
    id: str = Field(description="Unique game identifier")
    scenario_id: str = Field(description="Scenario this game is based on")

    # Game state
    turn_number: int = Field(ge=1, default=1, description="Current turn number")
    phase: GamePhase = Field(default=GamePhase.PLANNING, description="Current game phase")

    # Map and environment
    map_width: int = Field(ge=1, description="Map width in hexes")
    map_height: int = Field(ge=1, description="Map height in hexes")
    wind_direction: WindDirection = Field(description="Current wind direction")

    # Ships
    ships: dict[str, Ship] = Field(description="All ships indexed by ship_id")

    # Current turn orders
    p1_orders: TurnOrders | None = Field(default=None, description="P1 orders for current turn")
    p2_orders: TurnOrders | None = Field(default=None, description="P2 orders for current turn")

    # Event log
    event_log: list[EventLogEntry] = Field(
        default_factory=list, description="Complete event history"
    )

    # Victory conditions
    turn_limit: int | None = Field(default=None, description="Maximum turns (None = unlimited)")
    victory_condition: str = Field(default="first_struck", description="Victory condition type")
    game_ended: bool = Field(default=False, description="Whether the game has ended")
    winner: str | None = Field(default=None, description="Winner side (P1, P2, or None for draw)")

    def get_ship(self, ship_id: str) -> Ship:
        """Get a ship by ID.

        Args:
            ship_id: The ship identifier

        Returns:
            The ship

        Raises:
            KeyError: If ship doesn't exist
        """
        return self.ships[ship_id]

    def get_ships_by_side(self, side: str) -> list[Ship]:
        """Get all ships for a given side.

        Args:
            side: The player side (P1 or P2)

        Returns:
            List of ships for that side
        """
        return [ship for ship in self.ships.values() if ship.side == side]

    def add_event(self, event: EventLogEntry) -> None:
        """Add an event to the log.

        Args:
            event: The event to add
        """
        self.event_log.append(event)
