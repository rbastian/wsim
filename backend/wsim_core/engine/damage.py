"""Damage application system.

This module applies hit results to ship tracks (hull, rigging, crew, marines, guns).
It handles:
- Track depletion without going negative
- Struck status when hull or crew reaches critical levels
- Gun damage distribution across broadsides
- Damage event creation for event log
"""

from pydantic import BaseModel, Field

from ..models.common import AimPoint, Broadside
from ..models.events import EventLogEntry
from ..models.ship import Ship
from .combat import HitResult


class DamageApplication(BaseModel):
    """Result of applying damage to a ship.

    Attributes:
        hull_damage: Hull points lost
        rigging_damage: Rigging points lost
        crew_lost: Crew points lost
        marines_lost: Marines lost
        guns_lost_L: Guns lost on left broadside
        guns_lost_R: Guns lost on right broadside
        struck: Whether ship became struck due to this damage
        previous_hull: Hull value before damage
        previous_rigging: Rigging value before damage
        previous_crew: Crew value before damage
        previous_marines: Marines value before damage
        previous_guns_L: Left guns before damage
        previous_guns_R: Right guns before damage
    """

    hull_damage: int = Field(ge=0, description="Hull damage taken")
    rigging_damage: int = Field(ge=0, description="Rigging damage taken")
    crew_lost: int = Field(ge=0, description="Crew lost")
    marines_lost: int = Field(ge=0, description="Marines lost")
    guns_lost_L: int = Field(ge=0, description="Guns lost on left broadside")  # noqa: N815
    guns_lost_R: int = Field(ge=0, description="Guns lost on right broadside")  # noqa: N815
    struck: bool = Field(description="Ship became struck")

    # Previous values for event logging
    previous_hull: int = Field(ge=0)
    previous_rigging: int = Field(ge=0)
    previous_crew: int = Field(ge=0)
    previous_marines: int = Field(ge=0)
    previous_guns_L: int = Field(ge=0)  # noqa: N815
    previous_guns_R: int = Field(ge=0)  # noqa: N815


def apply_hit_result_to_ship(
    ship: Ship,
    hit_result: HitResult,
    aim: AimPoint,
    target_broadside: Broadside | None = None,
) -> DamageApplication:
    """Apply combat hit results to a ship's tracks.

    This function:
    1. Records pre-damage state
    2. Applies damage to the appropriate tracks based on aim point
    3. Distributes casualties between crew and marines
    4. Distributes gun damage across broadsides
    5. Checks for struck condition
    6. Prevents negative track values

    Args:
        ship: Ship to apply damage to (will be modified in place)
        hit_result: Hit result from combat resolution
        aim: Where the firing ship was aiming (hull or rigging)
        target_broadside: Which broadside was hit (for gun damage). If None, distributes evenly.

    Returns:
        DamageApplication record with all changes made
    """
    # Record previous state
    prev_hull = ship.hull
    prev_rigging = ship.rigging
    prev_crew = ship.crew
    prev_marines = ship.marines
    prev_guns_L = ship.guns_L  # noqa: N806
    prev_guns_R = ship.guns_R  # noqa: N806

    # Initialize damage counters
    hull_damage = 0
    rigging_damage = 0
    crew_lost = 0
    marines_lost = 0
    guns_lost_L = 0  # noqa: N806
    guns_lost_R = 0  # noqa: N806

    # Apply damage based on aim point
    if aim == AimPoint.HULL:
        # Hull hits
        hull_damage = min(hit_result.hits, ship.hull)
        ship.hull = max(0, ship.hull - hit_result.hits)

        # Crew casualties - prefer marines first, then crew
        remaining_casualties = hit_result.crew_casualties
        if remaining_casualties > 0:
            # Apply to marines first
            marines_killed = min(remaining_casualties, ship.marines)
            ship.marines = max(0, ship.marines - marines_killed)
            marines_lost = marines_killed
            remaining_casualties -= marines_killed

            # Then apply remaining to crew
            if remaining_casualties > 0:
                crew_killed = min(remaining_casualties, ship.crew)
                ship.crew = max(0, ship.crew - crew_killed)
                crew_lost = crew_killed

        # Gun damage
        if hit_result.gun_damage > 0:
            guns_lost_L, guns_lost_R = _apply_gun_damage(  # noqa: N806
                ship, hit_result.gun_damage, target_broadside
            )

    elif aim == AimPoint.RIGGING:
        # Rigging hits
        rigging_damage = min(hit_result.hits, ship.rigging)
        ship.rigging = max(0, ship.rigging - hit_result.hits)

    # Check for struck condition
    struck = _check_struck_condition(ship, prev_hull, prev_crew)
    if struck:
        ship.struck = True

    return DamageApplication(
        hull_damage=hull_damage,
        rigging_damage=rigging_damage,
        crew_lost=crew_lost,
        marines_lost=marines_lost,
        guns_lost_L=guns_lost_L,
        guns_lost_R=guns_lost_R,
        struck=struck,
        previous_hull=prev_hull,
        previous_rigging=prev_rigging,
        previous_crew=prev_crew,
        previous_marines=prev_marines,
        previous_guns_L=prev_guns_L,
        previous_guns_R=prev_guns_R,
    )


def _apply_gun_damage(
    ship: Ship, gun_damage: int, target_broadside: Broadside | None
) -> tuple[int, int]:
    """Distribute gun damage across broadsides.

    Args:
        ship: Ship losing guns (modified in place)
        gun_damage: Total guns to lose
        target_broadside: Which broadside was hit (None = distribute evenly)

    Returns:
        Tuple of (guns_lost_L, guns_lost_R)
    """
    guns_lost_L = 0  # noqa: N806
    guns_lost_R = 0  # noqa: N806

    if target_broadside == Broadside.L:
        # All damage to left
        guns_lost_L = min(gun_damage, ship.guns_L)  # noqa: N806
        ship.guns_L = max(0, ship.guns_L - gun_damage)
    elif target_broadside == Broadside.R:
        # All damage to right
        guns_lost_R = min(gun_damage, ship.guns_R)  # noqa: N806
        ship.guns_R = max(0, ship.guns_R - gun_damage)
    else:
        # Distribute evenly, starting with left for odd numbers
        remaining = gun_damage
        while remaining > 0 and (ship.guns_L > 0 or ship.guns_R > 0):
            if ship.guns_L > 0:
                ship.guns_L -= 1
                guns_lost_L += 1  # noqa: N806
                remaining -= 1
            if remaining > 0 and ship.guns_R > 0:
                ship.guns_R -= 1
                guns_lost_R += 1  # noqa: N806
                remaining -= 1

    return guns_lost_L, guns_lost_R


def _check_struck_condition(ship: Ship, previous_hull: int, previous_crew: int) -> bool:
    """Check if a ship should strike (surrender) due to damage.

    A ship strikes when:
    - Hull drops to 0 (ship is sinking)
    - Crew + Marines drops to 0 (no one to fight the ship)

    Args:
        ship: Ship to check (current state after damage)
        previous_hull: Hull value before damage
        previous_crew: Crew value before damage

    Returns:
        True if ship should strike
    """
    # Check if hull just dropped to 0
    if ship.hull == 0 and previous_hull > 0:
        return True

    # Check if crew+marines just dropped to 0
    current_total = ship.crew + ship.marines
    return current_total == 0


def create_damage_event(
    firing_ship_id: str,
    target_ship_id: str,
    broadside: Broadside,
    aim: AimPoint,
    hit_result: HitResult,
    damage: DamageApplication,
    turn_number: int,
) -> EventLogEntry:
    """Create an event log entry for damage application.

    Args:
        firing_ship_id: ID of ship that fired
        target_ship_id: ID of ship that was hit
        broadside: Which broadside fired
        aim: Hull or rigging
        hit_result: Combat hit results
        damage: Damage application results
        turn_number: Current turn number

    Returns:
        EventLogEntry for this damage event
    """
    from ..models.common import GamePhase

    # Build summary text
    summary_parts = [f"{firing_ship_id} fires {broadside.value} broadside at {target_ship_id}"]
    summary_parts.append(
        f"({aim.value} aim, {hit_result.range} hexes, {hit_result.range_bracket} range)"
    )

    if hit_result.hits > 0:
        if aim == AimPoint.HULL:
            summary_parts.append(f"→ {damage.hull_damage} hull damage")
            if damage.crew_lost > 0 or damage.marines_lost > 0:
                summary_parts.append(
                    f"→ {damage.crew_lost} crew + {damage.marines_lost} marines casualties"
                )
            if damage.guns_lost_L > 0 or damage.guns_lost_R > 0:
                summary_parts.append(f"→ {damage.guns_lost_L + damage.guns_lost_R} guns destroyed")
        else:
            summary_parts.append(f"→ {damage.rigging_damage} rigging damage")
    else:
        summary_parts.append("→ No hits")

    if damage.struck:
        summary_parts.append(f"→ {target_ship_id} STRUCK!")

    summary = ". ".join(summary_parts)

    # Build state diff
    state_diff = {
        "target_ship_id": target_ship_id,
        "hull": {
            "before": damage.previous_hull,
            "after": damage.previous_hull - damage.hull_damage,
        },
        "rigging": {
            "before": damage.previous_rigging,
            "after": damage.previous_rigging - damage.rigging_damage,
        },
        "crew": {"before": damage.previous_crew, "after": damage.previous_crew - damage.crew_lost},
        "marines": {
            "before": damage.previous_marines,
            "after": damage.previous_marines - damage.marines_lost,
        },
        "guns_L": {
            "before": damage.previous_guns_L,
            "after": damage.previous_guns_L - damage.guns_lost_L,
        },
        "guns_R": {
            "before": damage.previous_guns_R,
            "after": damage.previous_guns_R - damage.guns_lost_R,
        },
    }

    if damage.struck:
        state_diff["struck"] = True

    return EventLogEntry(
        turn_number=turn_number,
        phase=GamePhase.COMBAT,
        event_type="damage",
        summary=summary,
        modifiers=hit_result.modifiers_applied,
        state_diff=state_diff,
        metadata={
            "firing_ship_id": firing_ship_id,
            "target_ship_id": target_ship_id,
            "broadside": broadside.value,
            "aim": aim.value,
            "range": hit_result.range,
            "range_bracket": hit_result.range_bracket,
            "total_hits": hit_result.hits,
            "die_rolls": hit_result.die_rolls,
        },
    )
