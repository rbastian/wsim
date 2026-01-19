"""Broadside arc calculation for combat targeting.

This module determines which hexes are within a ship's broadside firing arcs.
Ships fire broadsides perpendicular to their facing direction.
"""

from ..models.common import Broadside, Facing
from ..models.hex import HexCoord
from ..models.ship import Ship


def get_broadside_arc_hexes(ship: Ship, broadside: Broadside, max_range: int = 10) -> set[HexCoord]:
    """Calculate which hexes are in a ship's broadside firing arc.

    Broadsides fire perpendicular to the ship's facing direction.
    Left broadside fires to port (left), right broadside fires to starboard (right).

    The arc extends perpendicular from the ship's center line, covering hexes
    that are roughly at a right angle to the ship's facing.

    Args:
        ship: The ship whose broadside arc to calculate
        broadside: Which broadside (L or R) to calculate arc for
        max_range: Maximum range in hexes (default 10 for typical game ranges)

    Returns:
        Set of hex coordinates that are within the broadside arc
    """
    # Determine perpendicular directions based on ship facing and broadside
    # Left broadside fires to port (counterclockwise perpendicular)
    # Right broadside fires to starboard (clockwise perpendicular)

    arc_directions = _get_broadside_directions(ship.facing, broadside)

    # Start from ship center (we'll use bow as approximation since ships are 2-hex)
    # In the future, might want to consider firing from both bow and stern
    center_hex = ship.bow_hex

    # Collect all hexes in the arc
    arc_hexes: set[HexCoord] = set()

    # For each primary arc direction, fan out in a cone
    for direction in arc_directions:
        # Trace outward from center in this direction up to max_range
        _trace_arc_cone(center_hex, direction, max_range, arc_hexes)

    return arc_hexes


def _get_broadside_directions(facing: Facing, broadside: Broadside) -> list[Facing]:
    """Get the primary directions for a broadside arc.

    Returns the perpendicular directions to the ship's facing.
    For each broadside, we return the three directions that form
    a ~90 degree cone perpendicular to the ship's facing.

    Args:
        facing: Ship's facing direction
        broadside: Which broadside (L or R)

    Returns:
        List of 3 facing directions that define the broadside arc
    """
    # Define perpendicular directions for each facing
    # Each entry is (left_broadside_directions, right_broadside_directions)
    perpendicular_map: dict[Facing, tuple[list[Facing], list[Facing]]] = {
        Facing.N: ([Facing.W, Facing.NW, Facing.SW], [Facing.E, Facing.NE, Facing.SE]),
        Facing.NE: ([Facing.NW, Facing.N, Facing.W], [Facing.SE, Facing.S, Facing.E]),
        Facing.E: ([Facing.N, Facing.NE, Facing.NW], [Facing.S, Facing.SE, Facing.SW]),
        Facing.SE: ([Facing.NE, Facing.E, Facing.N], [Facing.SW, Facing.W, Facing.S]),
        Facing.S: ([Facing.E, Facing.SE, Facing.NE], [Facing.W, Facing.SW, Facing.NW]),
        Facing.SW: ([Facing.SE, Facing.S, Facing.E], [Facing.NW, Facing.N, Facing.W]),
        Facing.W: ([Facing.S, Facing.SW, Facing.SE], [Facing.N, Facing.NW, Facing.NE]),
        Facing.NW: ([Facing.SW, Facing.W, Facing.S], [Facing.NE, Facing.E, Facing.N]),
    }

    left_dirs, right_dirs = perpendicular_map[facing]
    return left_dirs if broadside == Broadside.L else right_dirs


def _trace_arc_cone(
    start_hex: HexCoord, direction: Facing, max_range: int, arc_hexes: set[HexCoord]
) -> None:
    """Trace outward from start hex in a direction, adding hexes to arc.

    This creates a cone effect by including hexes in the general direction,
    not just a straight line.

    Args:
        start_hex: Starting hex coordinate
        direction: Direction to trace
        max_range: Maximum distance to trace
        arc_hexes: Set to add discovered hexes to (modified in place)
    """
    from .movement_executor import get_adjacent_hex

    # Trace straight out in the primary direction
    current = start_hex
    for distance in range(1, max_range + 1):
        try:
            current = get_adjacent_hex(current, direction)
            arc_hexes.add(current)

            # Add adjacent hexes to create a cone effect
            # This makes the arc wider as it extends
            if distance > 1:  # Don't widen at immediate adjacent hex
                # Get the two adjacent directions to create cone spread
                adjacent_dirs = _get_adjacent_directions(direction)
                for adj_dir in adjacent_dirs:
                    try:
                        # Add one hex in each adjacent direction to widen the cone
                        side_hex = get_adjacent_hex(current, adj_dir)
                        arc_hexes.add(side_hex)
                    except Exception:
                        # Skip hexes that go out of bounds (negative coordinates)
                        pass
        except Exception:
            # Stop tracing if we go out of bounds
            break


def _get_adjacent_directions(direction: Facing) -> list[Facing]:
    """Get the two directions adjacent to a given direction.

    For creating a cone effect in arc calculations.

    Args:
        direction: Base direction

    Returns:
        List of two adjacent directions (one on each side)
    """
    # Clockwise order of all directions
    all_directions = [
        Facing.N,
        Facing.NE,
        Facing.E,
        Facing.SE,
        Facing.S,
        Facing.SW,
        Facing.W,
        Facing.NW,
    ]

    idx = all_directions.index(direction)

    # Get previous and next directions (wrapping around)
    prev_idx = (idx - 1) % len(all_directions)
    next_idx = (idx + 1) % len(all_directions)

    return [all_directions[prev_idx], all_directions[next_idx]]


def hex_distance(hex1: HexCoord, hex2: HexCoord) -> int:
    """Calculate the distance between two hexes in hex grid.

    Uses cube coordinates internally for accurate hex distance calculation.

    Args:
        hex1: First hex coordinate
        hex2: Second hex coordinate

    Returns:
        Distance in hexes
    """
    # Convert from odd-q offset coordinates to cube coordinates
    # odd-q: col = x, row = y
    # cube: q = x, r = y - (x - (x&1)) / 2, s = -q - r

    def offset_to_cube(hex_coord: HexCoord) -> tuple[int, int, int]:
        q = hex_coord.col
        r = hex_coord.row - (hex_coord.col - (hex_coord.col & 1)) // 2
        s = -q - r
        return (q, r, s)

    q1, r1, s1 = offset_to_cube(hex1)
    q2, r2, s2 = offset_to_cube(hex2)

    # Distance in cube coordinates is (|q1-q2| + |r1-r2| + |s1-s2|) / 2
    return (abs(q1 - q2) + abs(r1 - r2) + abs(s1 - s2)) // 2


def is_hex_in_broadside_arc(
    ship: Ship, target_hex: HexCoord, broadside: Broadside, max_range: int = 10
) -> bool:
    """Check if a specific hex is within a ship's broadside arc.

    Args:
        ship: The firing ship
        target_hex: The hex to check
        broadside: Which broadside (L or R) to check
        max_range: Maximum range in hexes

    Returns:
        True if target_hex is in the broadside arc, False otherwise
    """
    # Quick range check first
    distance = hex_distance(ship.bow_hex, target_hex)
    if distance > max_range or distance == 0:
        return False

    # Get all hexes in arc
    arc_hexes = get_broadside_arc_hexes(ship, broadside, max_range)

    return target_hex in arc_hexes
