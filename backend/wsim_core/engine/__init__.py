"""Core game engine logic."""

from .movement_executor import (
    MovementExecutionError,
    MovementExecutionResult,
    ShipMovementState,
    calculate_stern_from_bow,
    execute_ship_forward_movement,
    execute_ship_turn,
    execute_simultaneous_movement,
    get_adjacent_hex,
    turn_left,
    turn_right,
)
from .movement_parser import (
    MovementAction,
    MovementActionType,
    MovementParseError,
    ParsedMovement,
    parse_movement,
    validate_movement_within_allowance,
)

__all__ = [
    # Movement parser
    "MovementAction",
    "MovementActionType",
    "MovementParseError",
    "ParsedMovement",
    "parse_movement",
    "validate_movement_within_allowance",
    # Movement executor
    "MovementExecutionError",
    "MovementExecutionResult",
    "ShipMovementState",
    "calculate_stern_from_bow",
    "execute_ship_forward_movement",
    "execute_ship_turn",
    "execute_simultaneous_movement",
    "get_adjacent_hex",
    "turn_left",
    "turn_right",
]
