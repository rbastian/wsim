"""Movement notation parser and validator.

This module parses movement notation strings (e.g., 'L1R1', '0', 'LLR2')
into a sequence of atomic movement actions that can be executed step-by-step.
"""

from enum import Enum

from pydantic import BaseModel, Field


class MovementActionType(str, Enum):
    """Types of atomic movement actions."""

    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"
    MOVE_FORWARD = "move_forward"
    NO_MOVEMENT = "no_movement"


class MovementAction(BaseModel):
    """A single atomic movement action."""

    action_type: MovementActionType = Field(description="Type of movement action")
    distance: int = Field(default=1, ge=0, description="Distance for forward movement")

    def __repr__(self) -> str:
        """String representation of the action."""
        if self.action_type == MovementActionType.MOVE_FORWARD:
            return f"MovementAction(MOVE_FORWARD, {self.distance})"
        return f"MovementAction({self.action_type.value.upper()})"


class ParsedMovement(BaseModel):
    """Result of parsing a movement notation string."""

    original_notation: str = Field(description="Original movement notation string")
    actions: list[MovementAction] = Field(description="Sequence of atomic actions")
    total_forward_hexes: int = Field(ge=0, description="Total forward movement hexes")

    def __repr__(self) -> str:
        """String representation of parsed movement."""
        return (
            f"ParsedMovement('{self.original_notation}' -> "
            f"{len(self.actions)} actions, {self.total_forward_hexes} hexes)"
        )


class MovementParseError(Exception):
    """Raised when movement notation parsing fails."""

    pass


def parse_movement(notation: str) -> ParsedMovement:
    """Parse a movement notation string into a sequence of actions.

    Valid notation consists of:
    - '0': No movement
    - 'L': Turn left
    - 'R': Turn right
    - Digits 1-9: Move forward that many hexes (each digit is a separate move action)

    Examples:
        - '0' -> no movement
        - 'L' -> turn left
        - 'L1R1' -> turn left, move 1, turn right, move 1
        - 'LLR2' -> turn left, turn left, turn right, move 2
        - '3' -> move 3 hexes forward

    Args:
        notation: The movement notation string

    Returns:
        ParsedMovement object with the sequence of actions

    Raises:
        MovementParseError: If the notation is invalid
    """
    if not notation:
        raise MovementParseError("Movement notation cannot be empty")

    # Normalize: strip whitespace and convert to uppercase
    notation = notation.strip().upper()

    if not notation:
        raise MovementParseError("Movement notation cannot be empty after stripping whitespace")

    # Special case: '0' means no movement
    if notation == "0":
        return ParsedMovement(
            original_notation=notation,
            actions=[MovementAction(action_type=MovementActionType.NO_MOVEMENT, distance=0)],
            total_forward_hexes=0,
        )

    # Parse character by character
    actions: list[MovementAction] = []
    total_forward_hexes = 0

    for i, char in enumerate(notation):
        if char == "L":
            actions.append(MovementAction(action_type=MovementActionType.TURN_LEFT))
        elif char == "R":
            actions.append(MovementAction(action_type=MovementActionType.TURN_RIGHT))
        elif char.isdigit():
            distance = int(char)
            if distance == 0:
                raise MovementParseError(
                    f"Invalid movement notation '{notation}': '0' can only appear alone, "
                    f"not as part of a sequence (position {i})"
                )
            # Each digit represents forward movement of that many hexes
            actions.append(
                MovementAction(action_type=MovementActionType.MOVE_FORWARD, distance=distance)
            )
            total_forward_hexes += distance
        else:
            raise MovementParseError(
                f"Invalid character '{char}' at position {i} in movement notation '{notation}'. "
                f"Valid characters are: L, R, 0-9"
            )

    if not actions:
        raise MovementParseError(f"Movement notation '{notation}' produced no actions")

    return ParsedMovement(
        original_notation=notation, actions=actions, total_forward_hexes=total_forward_hexes
    )


def validate_movement_within_allowance(
    parsed_movement: ParsedMovement, movement_allowance: int
) -> None:
    """Validate that parsed movement doesn't exceed the ship's movement allowance.

    Args:
        parsed_movement: The parsed movement to validate
        movement_allowance: The ship's movement allowance (e.g., battle_sail_speed)

    Raises:
        MovementParseError: If movement exceeds allowance
    """
    if parsed_movement.total_forward_hexes > movement_allowance:
        raise MovementParseError(
            f"Movement notation '{parsed_movement.original_notation}' requires "
            f"{parsed_movement.total_forward_hexes} hexes but ship only has "
            f"{movement_allowance} movement allowance"
        )
