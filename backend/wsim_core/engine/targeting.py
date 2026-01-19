"""Target selection logic with closest-target rule enforcement.

This module implements the WS&IM closest-target rule for broadside combat.
Ships can only fire at the closest enemy ship in their firing arc.
"""

from ..models.common import Broadside
from ..models.hex import HexCoord
from ..models.ship import Ship
from .arc import get_broadside_arc_hexes, hex_distance


class TargetInfo:
    """Information about a potential target ship.

    Attributes:
        ship: The target ship
        distance: Distance in hexes from firing ship
        hex_position: The hex position we're checking (bow or stern)
    """

    def __init__(self, ship: Ship, distance: int, hex_position: HexCoord):
        self.ship = ship
        self.distance = distance
        self.hex_position = hex_position

    def __repr__(self) -> str:
        return f"TargetInfo(ship={self.ship.id}, distance={self.distance})"


def get_ships_in_arc(
    firing_ship: Ship,
    all_ships: list[Ship],
    broadside: Broadside,
    max_range: int = 10,
) -> list[TargetInfo]:
    """Get all ships (any part) within a broadside's firing arc.

    A ship is considered in arc if either its bow or stern hex is in the arc.

    Args:
        firing_ship: The ship doing the firing
        all_ships: All ships in the game
        broadside: Which broadside (L or R) to check
        max_range: Maximum firing range in hexes

    Returns:
        List of TargetInfo for ships in arc (including the firing ship itself,
        friendly ships, struck ships, etc.). Caller must filter as needed.
    """
    arc_hexes = get_broadside_arc_hexes(firing_ship, broadside, max_range)

    targets_in_arc: list[TargetInfo] = []

    for ship in all_ships:
        # Skip the firing ship itself
        if ship.id == firing_ship.id:
            continue

        # Check if bow is in arc
        bow_distance = hex_distance(firing_ship.bow_hex, ship.bow_hex)
        if ship.bow_hex in arc_hexes:
            targets_in_arc.append(TargetInfo(ship, bow_distance, ship.bow_hex))
            continue  # Only add ship once even if both bow and stern are in arc

        # Check if stern is in arc
        stern_distance = hex_distance(firing_ship.bow_hex, ship.stern_hex)
        if ship.stern_hex in arc_hexes:
            targets_in_arc.append(TargetInfo(ship, stern_distance, ship.stern_hex))

    return targets_in_arc


def get_closest_enemy_in_arc(
    firing_ship: Ship,
    all_ships: list[Ship],
    broadside: Broadside,
    max_range: int = 10,
) -> Ship | None:
    """Get the closest enemy ship in firing arc, per closest-target rule.

    This implements the core WS&IM targeting restriction:
    - Only enemy ships are valid targets
    - Must be in the broadside's firing arc
    - Only the CLOSEST enemy can be targeted
    - Struck ships cannot be targeted
    - If multiple enemies are equidistant, any can be chosen (implementation picks first)

    Args:
        firing_ship: The ship doing the firing
        all_ships: All ships in the game
        broadside: Which broadside (L or R) to fire
        max_range: Maximum firing range in hexes

    Returns:
        The closest enemy ship if one exists in arc, None otherwise
    """
    # Get all ships in arc
    ships_in_arc = get_ships_in_arc(firing_ship, all_ships, broadside, max_range)

    # Filter to enemies only (different side, not struck)
    enemy_targets = [
        target
        for target in ships_in_arc
        if target.ship.side != firing_ship.side and not target.ship.struck
    ]

    # If no enemies in arc, no valid target
    if not enemy_targets:
        return None

    # Find the closest enemy
    closest = min(enemy_targets, key=lambda t: t.distance)

    return closest.ship


def get_all_valid_targets(
    firing_ship: Ship,
    all_ships: list[Ship],
    broadside: Broadside,
    max_range: int = 10,
) -> list[Ship]:
    """Get all valid targets for a broadside (enforcing closest-target rule).

    In the standard rules, this returns a list with at most one ship
    (the closest enemy). However, in cases of equal distance, multiple
    ships might be valid targets.

    This function is useful for UI purposes to show which ships can be targeted.

    Args:
        firing_ship: The ship doing the firing
        all_ships: All ships in the game
        broadside: Which broadside (L or R) to fire
        max_range: Maximum firing range in hexes

    Returns:
        List of valid target ships (usually 0 or 1 ship, possibly more if equidistant)
    """
    # Get all ships in arc
    ships_in_arc = get_ships_in_arc(firing_ship, all_ships, broadside, max_range)

    # Filter to enemies only (different side, not struck)
    enemy_targets = [
        target
        for target in ships_in_arc
        if target.ship.side != firing_ship.side and not target.ship.struck
    ]

    # If no enemies in arc, no valid targets
    if not enemy_targets:
        return []

    # Find minimum distance
    min_distance = min(target.distance for target in enemy_targets)

    # Return all enemies at minimum distance
    closest_enemies = [target.ship for target in enemy_targets if target.distance == min_distance]

    return closest_enemies


def is_valid_target(
    firing_ship: Ship,
    target_ship: Ship,
    all_ships: list[Ship],
    broadside: Broadside,
    max_range: int = 10,
) -> bool:
    """Check if a specific ship is a valid target for firing.

    Validates that:
    - Target is in the firing arc
    - Target is an enemy (different side)
    - Target is not struck
    - Target is the closest enemy (closest-target rule)

    Args:
        firing_ship: The ship doing the firing
        target_ship: The proposed target
        all_ships: All ships in the game
        broadside: Which broadside (L or R) to fire
        max_range: Maximum firing range in hexes

    Returns:
        True if the target is valid, False otherwise
    """
    # Basic checks first
    if target_ship.id == firing_ship.id:
        return False
    if target_ship.side == firing_ship.side:
        return False
    if target_ship.struck:
        return False

    # Get all valid targets
    valid_targets = get_all_valid_targets(firing_ship, all_ships, broadside, max_range)

    # Check if target_ship is in the list of valid targets
    return any(ship.id == target_ship.id for ship in valid_targets)


def get_targeting_info(
    firing_ship: Ship,
    all_ships: list[Ship],
    broadside: Broadside,
    max_range: int = 10,
) -> dict[str, object]:
    """Get detailed targeting information for debugging/UI purposes.

    Returns comprehensive information about what's in arc and why targets
    are valid or invalid.

    Args:
        firing_ship: The ship doing the firing
        all_ships: All ships in the game
        broadside: Which broadside (L or R)
        max_range: Maximum firing range in hexes

    Returns:
        Dictionary containing:
        - ships_in_arc: All ships (any side) in the firing arc
        - enemy_ships_in_arc: Enemy ships in arc (including struck)
        - valid_targets: Ships that can be legally targeted
        - closest_distance: Distance to closest enemy (if any)
    """
    ships_in_arc = get_ships_in_arc(firing_ship, all_ships, broadside, max_range)

    enemy_ships_in_arc = [target for target in ships_in_arc if target.ship.side != firing_ship.side]

    valid_targets = get_all_valid_targets(firing_ship, all_ships, broadside, max_range)

    closest_distance = None
    if enemy_ships_in_arc:
        # Include struck ships when finding closest distance for info purposes
        active_enemies = [t for t in enemy_ships_in_arc if not t.ship.struck]
        if active_enemies:
            closest_distance = min(t.distance for t in active_enemies)

    return {
        "ships_in_arc": [t.ship.id for t in ships_in_arc],
        "enemy_ships_in_arc": [t.ship.id for t in enemy_ships_in_arc],
        "valid_targets": [ship.id for ship in valid_targets],
        "closest_distance": closest_distance,
    }
