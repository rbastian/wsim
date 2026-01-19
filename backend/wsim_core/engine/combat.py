"""Combat resolution engine with data-driven hit tables.

This module implements the WS&IM combat system:
- Loading hit tables from data files
- Resolving broadside firing using range, gun type, and aim
- Applying modifiers (range, crew quality)
- Calculating hits, crew casualties, and gun damage
"""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from ..models.common import AimPoint, Broadside
from ..models.ship import Ship
from .arc import hex_distance
from .rng import RNG


class HitResult(BaseModel):
    """Result of a single broadside firing.

    Attributes:
        hits: Number of hits on target (hull or rigging)
        crew_casualties: Number of crew lost
        gun_damage: Number of guns damaged
        range: Distance to target in hexes
        range_bracket: Range bracket (short/medium/long)
        die_rolls: List of die rolls made (for event log)
        modifiers_applied: Dict of modifiers applied
    """

    hits: int = Field(ge=0, description="Number of hits")
    crew_casualties: int = Field(ge=0, description="Crew lost")
    gun_damage: int = Field(ge=0, description="Guns damaged")
    range: int = Field(ge=0, description="Range in hexes")
    range_bracket: Literal["short", "medium", "long"] = Field(description="Range bracket")
    die_rolls: list[int] = Field(default_factory=list, description="Die rolls made")
    modifiers_applied: dict[str, int] = Field(default_factory=dict, description="Modifiers applied")


class HitTables:
    """Hit tables loader and lookup."""

    def __init__(self, tables_file: Path | None = None):
        """Initialize hit tables.

        Args:
            tables_file: Path to hit tables JSON file. If None, uses default.
        """
        if tables_file is None:
            # Default to tables/hit_tables.json relative to this file
            tables_dir = Path(__file__).parent.parent / "tables"
            tables_file = tables_dir / "hit_tables.json"

        with open(tables_file) as f:
            self.data = json.load(f)

    def get_range_bracket(self, distance: int) -> Literal["short", "medium", "long"]:
        """Get range bracket for a given distance.

        Args:
            distance: Distance in hexes

        Returns:
            Range bracket name
        """
        for bracket, info in self.data["range_brackets"].items():
            if info["min"] <= distance <= info["max"]:
                return bracket
        # Default to long if out of range
        return "long"

    def get_hits_for_roll(
        self,
        die_roll: int,
        range_bracket: Literal["short", "medium", "long"],
        aim: AimPoint,
    ) -> int:
        """Look up number of hits for a die roll.

        Args:
            die_roll: D6 result (1-6)
            range_bracket: Range bracket
            aim: Hull or rigging

        Returns:
            Number of hits for this roll
        """
        aim_key = aim.value  # "hull" or "rigging"
        table = self.data["hit_table"][aim_key][range_bracket]
        return table[str(die_roll)]

    def get_crew_casualties_for_roll(self, die_roll: int) -> int:
        """Look up crew casualties for a hull hit.

        Args:
            die_roll: D6 result (1-6)

        Returns:
            Number of crew casualties
        """
        return self.data["crew_casualties"][str(die_roll)]

    def get_gun_damage_for_roll(self, die_roll: int, at_short_range: bool) -> int:
        """Look up gun damage for a hull hit.

        Args:
            die_roll: D6 result (1-6)
            at_short_range: Whether firing was at short range

        Returns:
            Number of guns damaged (0 if not at short range)
        """
        if not at_short_range:
            return 0
        return self.data["gun_damage"]["short_range"][str(die_roll)]


def get_crew_quality_modifier(ship: Ship, initial_crew: int) -> int:
    """Calculate crew quality modifier based on casualties.

    Args:
        ship: Ship to check
        initial_crew: Ship's initial crew value

    Returns:
        Modifier to hit rolls (0, -1, or -2)
    """
    crew_ratio = ship.crew / initial_crew if initial_crew > 0 else 0

    if crew_ratio >= 0.75:  # At least 75% crew
        return 0
    elif crew_ratio >= 0.5:  # At least 50% crew
        return -1
    else:  # Less than 50% crew
        return -2


def resolve_broadside_fire(
    firing_ship: Ship,
    target_ship: Ship,
    broadside: Broadside,
    aim: AimPoint,
    rng: RNG,
    hit_tables: HitTables,
    initial_crew: int,
) -> HitResult:
    """Resolve a broadside firing and calculate hits.

    This function:
    1. Calculates range and range bracket
    2. Determines number of guns firing
    3. Applies crew quality modifier
    4. Rolls dice for each gun
    5. Looks up hits in tables
    6. If hull hits: rolls for crew casualties and gun damage

    Args:
        firing_ship: Ship doing the firing
        target_ship: Target ship
        broadside: Which broadside (L or R)
        aim: Hull or rigging
        rng: Random number generator
        hit_tables: Hit tables instance
        initial_crew: Firing ship's initial crew (for quality modifier)

    Returns:
        HitResult with all calculated values
    """
    # Calculate range
    distance = hex_distance(firing_ship.bow_hex, target_ship.bow_hex)
    range_bracket = hit_tables.get_range_bracket(distance)

    # Get number of guns (regular guns only in MVP, carronades would be separate)
    num_guns = firing_ship.guns_L if broadside == Broadside.L else firing_ship.guns_R

    # Calculate modifiers
    crew_modifier = get_crew_quality_modifier(firing_ship, initial_crew)
    modifiers = {
        "crew_quality": crew_modifier,
    }

    # Roll for each gun and accumulate hits
    total_hits = 0
    die_rolls = []

    for _ in range(num_guns):
        # Roll D6
        raw_roll = rng.roll_d6()
        die_rolls.append(raw_roll)

        # Apply modifiers (but clamp to valid die range 1-6)
        modified_roll = max(1, min(6, raw_roll + crew_modifier))

        # Look up hits
        hits = hit_tables.get_hits_for_roll(modified_roll, range_bracket, aim)
        total_hits += hits

    # If aiming at hull and got hits, roll for crew casualties and gun damage
    crew_casualties = 0
    gun_damage = 0

    if aim == AimPoint.HULL and total_hits > 0:
        # Roll once for crew casualties per hull hit
        for _ in range(total_hits):
            casualty_roll = rng.roll_d6()
            die_rolls.append(casualty_roll)
            crew_casualties += hit_tables.get_crew_casualties_for_roll(casualty_roll)

        # Roll for gun damage if at short range
        at_short_range = range_bracket == "short"
        if at_short_range:
            for _ in range(total_hits):
                gun_roll = rng.roll_d6()
                die_rolls.append(gun_roll)
                gun_damage += hit_tables.get_gun_damage_for_roll(gun_roll, at_short_range)

    return HitResult(
        hits=total_hits,
        crew_casualties=crew_casualties,
        gun_damage=gun_damage,
        range=distance,
        range_bracket=range_bracket,
        die_rolls=die_rolls,
        modifiers_applied=modifiers,
    )


def can_fire_broadside(ship: Ship, broadside: Broadside) -> bool:
    """Check if a ship can fire a broadside.

    Args:
        ship: Ship to check
        broadside: Which broadside

    Returns:
        True if broadside can fire
    """
    # Ship must not be struck
    if ship.struck:
        return False

    # Broadside must be loaded
    from ..models.common import LoadState

    load_state = ship.load_L if broadside == Broadside.L else ship.load_R
    if load_state == LoadState.EMPTY:
        return False

    # Must have at least one gun on that side
    num_guns = ship.guns_L if broadside == Broadside.L else ship.guns_R
    return num_guns > 0


def get_legal_targets(
    firing_ship: Ship, all_ships: dict[str, Ship], broadside: Broadside, max_range: int = 10
) -> list[Ship]:
    """Get legal targets for a broadside firing using the closest-target rule.

    The closest-target rule states that a ship must fire at the closest enemy ship
    in its broadside arc. This prevents firing at distant targets when closer enemies
    are present.

    Args:
        firing_ship: Ship doing the firing
        all_ships: Dictionary of all ships in the game (by ID)
        broadside: Which broadside (L or R) to check
        max_range: Maximum range in hexes (default 10)

    Returns:
        List of legal target ships (empty if no valid targets, or single ship if
        closest-target rule applies, or multiple ships if tied for closest)
    """
    from .arc import get_broadside_arc_hexes, hex_distance

    # Get all hexes in the broadside arc
    arc_hexes = get_broadside_arc_hexes(firing_ship, broadside, max_range)

    # Find all enemy ships in arc (that are not struck)
    enemy_ships_in_arc: list[tuple[Ship, int]] = []

    for ship in all_ships.values():
        # Skip self
        if ship.id == firing_ship.id:
            continue

        # Skip friendly ships (same side)
        if ship.side == firing_ship.side:
            continue

        # Skip struck ships (can't be targeted)
        if ship.struck:
            continue

        # Check if ship's bow or stern is in arc
        if ship.bow_hex in arc_hexes or ship.stern_hex in arc_hexes:
            distance = hex_distance(firing_ship.bow_hex, ship.bow_hex)
            if distance <= max_range:
                enemy_ships_in_arc.append((ship, distance))

    # If no enemies in arc, return empty list
    if not enemy_ships_in_arc:
        return []

    # Apply closest-target rule: must fire at closest enemy
    min_distance = min(distance for _, distance in enemy_ships_in_arc)
    closest_ships = [ship for ship, distance in enemy_ships_in_arc if distance == min_distance]

    return closest_ships


def apply_damage(ship: Ship, hit_result: HitResult, aim: AimPoint, broadside: Broadside) -> None:
    """Apply damage to a ship from a broadside firing.

    This modifies the ship in place, updating hull/rigging, crew, and guns.
    Also updates struck status if hull reaches 0.

    Args:
        ship: Target ship to damage (modified in place)
        hit_result: Result from resolve_broadside_fire
        aim: Whether firing aimed at hull or rigging
        broadside: Which broadside was hit (for gun damage)
    """
    # Apply hits to hull or rigging
    if aim == AimPoint.HULL:
        ship.hull = max(0, ship.hull - hit_result.hits)
    else:  # AimPoint.RIGGING
        ship.rigging = max(0, ship.rigging - hit_result.hits)

    # Apply crew casualties (only for hull hits)
    if hit_result.crew_casualties > 0:
        ship.crew = max(0, ship.crew - hit_result.crew_casualties)

    # Apply gun damage (only at short range)
    if hit_result.gun_damage > 0:
        # Damage guns on the broadside that was hit
        # Note: broadside parameter is the FIRING ship's broadside, we need to determine
        # which broadside of the target ship faces the firing ship
        # For MVP, we'll apply damage to both broadsides proportionally
        total_guns = ship.guns_L + ship.guns_R
        if total_guns > 0:
            # Distribute damage proportionally
            damage_left = (hit_result.gun_damage * ship.guns_L) // total_guns
            damage_right = hit_result.gun_damage - damage_left
            ship.guns_L = max(0, ship.guns_L - damage_left)
            ship.guns_R = max(0, ship.guns_R - damage_right)

    # Check if ship should strike (hull reaches 0)
    if ship.hull <= 0:
        ship.struck = True
