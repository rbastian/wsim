"""Common types and enums used across models."""

from enum import Enum


class Side(str, Enum):
    """Player side identifier."""

    P1 = "P1"
    P2 = "P2"


class Facing(str, Enum):
    """Ship facing direction (hex direction)."""

    N = "N"
    NE = "NE"
    E = "E"
    SE = "SE"
    S = "S"
    SW = "SW"
    W = "W"
    NW = "NW"


class WindDirection(str, Enum):
    """Wind direction."""

    N = "N"
    NE = "NE"
    E = "E"
    SE = "SE"
    S = "S"
    SW = "SW"
    W = "W"
    NW = "NW"


class LoadState(str, Enum):
    """Broadside load state."""

    EMPTY = "E"  # Unloaded
    ROUNDSHOT = "R"  # Loaded with roundshot (beginner only ammo type)


class GamePhase(str, Enum):
    """Game phase within a turn."""

    PLANNING = "planning"
    MOVEMENT = "movement"
    COMBAT = "combat"
    RELOAD = "reload"


class Broadside(str, Enum):
    """Broadside identifier."""

    L = "L"  # Left
    R = "R"  # Right


class AimPoint(str, Enum):
    """Combat aim point."""

    HULL = "hull"
    RIGGING = "rigging"
