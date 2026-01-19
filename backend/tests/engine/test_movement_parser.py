"""Tests for movement notation parser."""

import pytest

from wsim_core.engine.movement_parser import (
    MovementAction,
    MovementActionType,
    MovementParseError,
    ParsedMovement,
    parse_movement,
    validate_movement_within_allowance,
)


class TestParseMovement:
    """Tests for parse_movement function."""

    def test_parse_no_movement(self):
        """Test parsing '0' for no movement."""
        result = parse_movement("0")
        assert result.original_notation == "0"
        assert len(result.actions) == 1
        assert result.actions[0].action_type == MovementActionType.NO_MOVEMENT
        assert result.total_forward_hexes == 0

    def test_parse_single_turn_left(self):
        """Test parsing a single left turn."""
        result = parse_movement("L")
        assert result.original_notation == "L"
        assert len(result.actions) == 1
        assert result.actions[0].action_type == MovementActionType.TURN_LEFT
        assert result.total_forward_hexes == 0

    def test_parse_single_turn_right(self):
        """Test parsing a single right turn."""
        result = parse_movement("R")
        assert result.original_notation == "R"
        assert len(result.actions) == 1
        assert result.actions[0].action_type == MovementActionType.TURN_RIGHT
        assert result.total_forward_hexes == 0

    def test_parse_single_forward_movement(self):
        """Test parsing single digit forward movement."""
        result = parse_movement("3")
        assert result.original_notation == "3"
        assert len(result.actions) == 1
        assert result.actions[0].action_type == MovementActionType.MOVE_FORWARD
        assert result.actions[0].distance == 3
        assert result.total_forward_hexes == 3

    def test_parse_multiple_turns(self):
        """Test parsing multiple consecutive turns."""
        result = parse_movement("LLR")
        assert result.original_notation == "LLR"
        assert len(result.actions) == 3
        assert result.actions[0].action_type == MovementActionType.TURN_LEFT
        assert result.actions[1].action_type == MovementActionType.TURN_LEFT
        assert result.actions[2].action_type == MovementActionType.TURN_RIGHT
        assert result.total_forward_hexes == 0

    def test_parse_turn_and_move(self):
        """Test parsing turn followed by forward movement."""
        result = parse_movement("L2")
        assert result.original_notation == "L2"
        assert len(result.actions) == 2
        assert result.actions[0].action_type == MovementActionType.TURN_LEFT
        assert result.actions[1].action_type == MovementActionType.MOVE_FORWARD
        assert result.actions[1].distance == 2
        assert result.total_forward_hexes == 2

    def test_parse_complex_sequence(self):
        """Test parsing complex movement sequence 'L1R1'."""
        result = parse_movement("L1R1")
        assert result.original_notation == "L1R1"
        assert len(result.actions) == 4
        assert result.actions[0].action_type == MovementActionType.TURN_LEFT
        assert result.actions[1].action_type == MovementActionType.MOVE_FORWARD
        assert result.actions[1].distance == 1
        assert result.actions[2].action_type == MovementActionType.TURN_RIGHT
        assert result.actions[3].action_type == MovementActionType.MOVE_FORWARD
        assert result.actions[3].distance == 1
        assert result.total_forward_hexes == 2

    def test_parse_llr2_sequence(self):
        """Test parsing 'LLR2' sequence."""
        result = parse_movement("LLR2")
        assert result.original_notation == "LLR2"
        assert len(result.actions) == 4
        assert result.actions[0].action_type == MovementActionType.TURN_LEFT
        assert result.actions[1].action_type == MovementActionType.TURN_LEFT
        assert result.actions[2].action_type == MovementActionType.TURN_RIGHT
        assert result.actions[3].action_type == MovementActionType.MOVE_FORWARD
        assert result.actions[3].distance == 2
        assert result.total_forward_hexes == 2

    def test_parse_multiple_forward_movements(self):
        """Test parsing multiple forward movements."""
        result = parse_movement("1R2L3")
        assert result.original_notation == "1R2L3"
        assert len(result.actions) == 5
        assert result.actions[0].action_type == MovementActionType.MOVE_FORWARD
        assert result.actions[0].distance == 1
        assert result.actions[1].action_type == MovementActionType.TURN_RIGHT
        assert result.actions[2].action_type == MovementActionType.MOVE_FORWARD
        assert result.actions[2].distance == 2
        assert result.actions[3].action_type == MovementActionType.TURN_LEFT
        assert result.actions[4].action_type == MovementActionType.MOVE_FORWARD
        assert result.actions[4].distance == 3
        assert result.total_forward_hexes == 6

    def test_parse_lowercase_input(self):
        """Test that lowercase input is normalized to uppercase."""
        result = parse_movement("l1r1")
        assert result.original_notation == "L1R1"
        assert len(result.actions) == 4

    def test_parse_with_whitespace(self):
        """Test that whitespace is stripped."""
        result = parse_movement("  L1R1  ")
        assert result.original_notation == "L1R1"
        assert len(result.actions) == 4

    def test_parse_max_digit(self):
        """Test parsing maximum single digit (9)."""
        result = parse_movement("9")
        assert result.actions[0].distance == 9
        assert result.total_forward_hexes == 9

    def test_parse_empty_string_error(self):
        """Test that empty string raises error."""
        with pytest.raises(MovementParseError, match="cannot be empty"):
            parse_movement("")

    def test_parse_whitespace_only_error(self):
        """Test that whitespace-only string raises error."""
        with pytest.raises(MovementParseError, match="cannot be empty after stripping"):
            parse_movement("   ")

    def test_parse_invalid_character_error(self):
        """Test that invalid characters raise error."""
        with pytest.raises(MovementParseError, match="Invalid character 'X'"):
            parse_movement("LXR")

    def test_parse_zero_in_sequence_error(self):
        """Test that '0' cannot appear in a sequence."""
        with pytest.raises(MovementParseError, match="'0' can only appear alone"):
            parse_movement("L0R")

    def test_parse_zero_in_sequence_error_position(self):
        """Test that error message includes position."""
        with pytest.raises(MovementParseError, match="position 1"):
            parse_movement("L0")

    def test_parse_invalid_symbol_error(self):
        """Test various invalid symbols."""
        invalid_notations = ["L-R", "L+1", "L*R", "L.R", "L,R", "L/R"]
        for notation in invalid_notations:
            with pytest.raises(MovementParseError, match="Invalid character"):
                parse_movement(notation)


class TestValidateMovementWithinAllowance:
    """Tests for validate_movement_within_allowance function."""

    def test_validate_within_allowance(self):
        """Test that movement within allowance passes validation."""
        parsed = parse_movement("L1R1")
        validate_movement_within_allowance(parsed, 4)  # Should not raise

    def test_validate_exact_allowance(self):
        """Test that movement exactly at allowance passes validation."""
        parsed = parse_movement("4")
        validate_movement_within_allowance(parsed, 4)  # Should not raise

    def test_validate_zero_movement(self):
        """Test that zero movement always passes validation."""
        parsed = parse_movement("0")
        validate_movement_within_allowance(parsed, 0)  # Should not raise
        validate_movement_within_allowance(parsed, 10)  # Should not raise

    def test_validate_turns_only(self):
        """Test that turns without forward movement pass validation."""
        parsed = parse_movement("LLR")
        validate_movement_within_allowance(parsed, 0)  # Should not raise

    def test_validate_exceeds_allowance_error(self):
        """Test that movement exceeding allowance raises error."""
        parsed = parse_movement("5")
        with pytest.raises(
            MovementParseError, match="requires 5 hexes but ship only has 4 movement allowance"
        ):
            validate_movement_within_allowance(parsed, 4)

    def test_validate_exceeds_allowance_complex(self):
        """Test that complex movement exceeding allowance raises error."""
        parsed = parse_movement("L2R2L1")
        with pytest.raises(
            MovementParseError, match="requires 5 hexes but ship only has 3 movement allowance"
        ):
            validate_movement_within_allowance(parsed, 3)


class TestMovementActionModel:
    """Tests for MovementAction Pydantic model."""

    def test_movement_action_turn_left(self):
        """Test creating a turn left action."""
        action = MovementAction(action_type=MovementActionType.TURN_LEFT)
        assert action.action_type == MovementActionType.TURN_LEFT
        assert action.distance == 1  # default

    def test_movement_action_move_forward(self):
        """Test creating a forward movement action."""
        action = MovementAction(action_type=MovementActionType.MOVE_FORWARD, distance=3)
        assert action.action_type == MovementActionType.MOVE_FORWARD
        assert action.distance == 3

    def test_movement_action_negative_distance_error(self):
        """Test that negative distance raises validation error."""
        with pytest.raises(ValueError):
            MovementAction(action_type=MovementActionType.MOVE_FORWARD, distance=-1)


class TestParsedMovementModel:
    """Tests for ParsedMovement Pydantic model."""

    def test_parsed_movement_model(self):
        """Test creating a ParsedMovement model."""
        actions = [
            MovementAction(action_type=MovementActionType.TURN_LEFT),
            MovementAction(action_type=MovementActionType.MOVE_FORWARD, distance=2),
        ]
        parsed = ParsedMovement(original_notation="L2", actions=actions, total_forward_hexes=2)
        assert parsed.original_notation == "L2"
        assert len(parsed.actions) == 2
        assert parsed.total_forward_hexes == 2

    def test_parsed_movement_negative_total_error(self):
        """Test that negative total_forward_hexes raises validation error."""
        with pytest.raises(ValueError):
            ParsedMovement(original_notation="test", actions=[], total_forward_hexes=-1)
