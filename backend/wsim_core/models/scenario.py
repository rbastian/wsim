"""Scenario definition models for loading scenarios from JSON."""

from pydantic import BaseModel, Field

from .common import Facing, LoadState, Side, WindDirection


class MapConfig(BaseModel):
    """Map dimensions."""

    width: int = Field(ge=1, description="Map width in hexes")
    height: int = Field(ge=1, description="Map height in hexes")


class WindConfig(BaseModel):
    """Wind configuration."""

    direction: WindDirection = Field(description="Wind direction")


class VictoryConfig(BaseModel):
    """Victory condition configuration."""

    type: str = Field(description="Victory condition type")
    metric: str | None = Field(default=None, description="Optional metric for scoring")


class ShipStartPosition(BaseModel):
    """Ship starting position."""

    bow: tuple[int, int] = Field(description="Bow hex [col, row]")
    facing: Facing = Field(description="Initial facing direction")


class ShipGuns(BaseModel):
    """Ship gun configuration."""

    L: int = Field(ge=0, description="Left broadside guns")
    R: int = Field(ge=0, description="Right broadside guns")


class ShipCarronades(BaseModel):
    """Ship carronade configuration."""

    L: int = Field(ge=0, default=0, description="Left broadside carronades")
    R: int = Field(ge=0, default=0, description="Right broadside carronades")


class ShipInitialLoad(BaseModel):
    """Initial load state for both broadsides."""

    L: LoadState = Field(description="Left broadside initial load")
    R: LoadState = Field(description="Right broadside initial load")


class ScenarioShip(BaseModel):
    """Ship definition in a scenario."""

    id: str = Field(description="Unique ship identifier")
    side: Side = Field(description="Player side")
    name: str = Field(description="Ship name")
    battle_sail_speed: int = Field(ge=1, description="Movement allowance at battle sails")
    start: ShipStartPosition = Field(description="Starting position")
    guns: ShipGuns = Field(description="Long guns per broadside")
    carronades: ShipCarronades = Field(
        default_factory=lambda: ShipCarronades(L=0, R=0), description="Carronades per broadside"
    )
    hull: int = Field(ge=1, description="Initial hull points")
    rigging: int = Field(ge=1, description="Initial rigging points")
    crew: int = Field(ge=1, description="Initial crew points")
    marines: int = Field(ge=0, description="Initial marine points")
    initial_load: ShipInitialLoad = Field(description="Initial broadside load state")


class Scenario(BaseModel):
    """Complete scenario definition.

    Defines all the initial setup for a game including map, wind, ships, and victory conditions.
    """

    id: str = Field(description="Unique scenario identifier")
    name: str = Field(description="Scenario name")
    description: str = Field(description="Scenario description")
    map: MapConfig = Field(description="Map configuration")
    wind: WindConfig = Field(description="Wind configuration")
    turn_limit: int | None = Field(default=None, description="Maximum turns (None = unlimited)")
    victory: VictoryConfig = Field(description="Victory conditions")
    ships: list[ScenarioShip] = Field(description="Ship definitions")

    def validate_ship_ids_unique(self) -> None:
        """Validate that all ship IDs are unique.

        Raises:
            ValueError: If duplicate ship IDs are found
        """
        ship_ids = [ship.id for ship in self.ships]
        if len(ship_ids) != len(set(ship_ids)):
            duplicates = [sid for sid in ship_ids if ship_ids.count(sid) > 1]
            raise ValueError(f"Duplicate ship IDs found: {set(duplicates)}")

    def validate_ships_in_bounds(self) -> None:
        """Validate that all ships start within map bounds.

        Raises:
            ValueError: If any ship starts outside map bounds
        """
        for ship in self.ships:
            col, row = ship.start.bow
            if not (0 <= col < self.map.width and 0 <= row < self.map.height):
                raise ValueError(
                    f"Ship {ship.id} bow position ({col}, {row}) "
                    f"is outside map bounds (0-{self.map.width - 1}, 0-{self.map.height - 1})"
                )
