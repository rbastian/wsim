"""Core game engine logic."""

from .arc import (
    get_broadside_arc_hexes,
    hex_distance,
    is_hex_in_broadside_arc,
)
from .collision import (
    CollisionDetectionError,
    CollisionResolution,
    CollisionResult,
    detect_and_resolve_collisions,
    detect_collisions,
    detect_hex_occupancy,
    get_ship_hexes,
    resolve_collision,
)
from .fouling import (
    FoulingResult,
    apply_fouling,
    check_and_apply_fouling,
    check_fouling,
)
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
from .rng import RNG, SeededRNG, UnseededRNG, create_rng
from .targeting import (
    TargetInfo,
    get_all_valid_targets,
    get_closest_enemy_in_arc,
    get_ships_in_arc,
    get_targeting_info,
    is_valid_target,
)

__all__ = [
    # Arc calculation
    "get_broadside_arc_hexes",
    "hex_distance",
    "is_hex_in_broadside_arc",
    # Targeting
    "TargetInfo",
    "get_all_valid_targets",
    "get_closest_enemy_in_arc",
    "get_ships_in_arc",
    "get_targeting_info",
    "is_valid_target",
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
    # Collision detection
    "CollisionDetectionError",
    "CollisionResolution",
    "CollisionResult",
    "detect_and_resolve_collisions",
    "detect_collisions",
    "detect_hex_occupancy",
    "get_ship_hexes",
    "resolve_collision",
    # Fouling
    "FoulingResult",
    "apply_fouling",
    "check_and_apply_fouling",
    "check_fouling",
    # RNG
    "RNG",
    "SeededRNG",
    "UnseededRNG",
    "create_rng",
]
