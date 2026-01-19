"""Ship model and related types."""

from pydantic import BaseModel, Field

from .common import Facing, LoadState, Side
from .hex import HexCoord


class Ship(BaseModel):
    """Ship state model.

    Represents a single ship with all its attributes, position, and status.
    """

    # Identity
    id: str = Field(description="Unique ship identifier")
    name: str = Field(description="Ship name")
    side: Side = Field(description="Player side (P1 or P2)")

    # Position
    bow_hex: HexCoord = Field(description="Bow hex position")
    stern_hex: HexCoord = Field(description="Stern hex position")
    facing: Facing = Field(description="Ship facing direction")

    # Movement stats
    battle_sail_speed: int = Field(ge=1, description="Movement allowance at battle sails")

    # Combat stats - guns
    guns_L: int = Field(ge=0, description="Long guns on left broadside")
    guns_R: int = Field(ge=0, description="Long guns on right broadside")
    carronades_L: int = Field(ge=0, default=0, description="Carronades on left broadside")
    carronades_R: int = Field(ge=0, default=0, description="Carronades on right broadside")

    # Tracks
    hull: int = Field(ge=0, description="Current hull points")
    rigging: int = Field(ge=0, description="Current rigging points")
    crew: int = Field(ge=0, description="Current crew points")
    marines: int = Field(ge=0, description="Current marine points")

    # Load state
    load_L: LoadState = Field(description="Left broadside load state")
    load_R: LoadState = Field(description="Right broadside load state")

    # Status flags
    fouled: bool = Field(default=False, description="Ship is fouled with another ship")
    struck: bool = Field(default=False, description="Ship has struck (surrendered)")

    # Movement tracking for drift rule
    turns_without_bow_advance: int = Field(
        ge=0, default=0, description="Consecutive turns without bow hex advancement"
    )
