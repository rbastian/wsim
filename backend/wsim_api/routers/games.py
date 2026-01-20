"""Game management API endpoints."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from wsim_core.engine.arc import get_broadside_arc_hexes
from wsim_core.engine.collision import detect_and_resolve_collisions
from wsim_core.engine.combat import (
    HitTables,
    apply_damage,
    can_fire_broadside,
    get_legal_targets,
    resolve_broadside_fire,
)
from wsim_core.engine.drift import check_and_apply_drift
from wsim_core.engine.movement_executor import execute_simultaneous_movement
from wsim_core.engine.movement_parser import (
    MovementParseError,
    parse_movement,
    validate_movement_within_allowance,
)
from wsim_core.engine.reload import create_reload_event, reload_all_ships
from wsim_core.engine.rng import create_rng
from wsim_core.engine.targeting import get_all_valid_targets, get_ships_in_arc
from wsim_core.models.common import AimPoint, Broadside, GamePhase, LoadState
from wsim_core.models.events import EventLogEntry
from wsim_core.models.game import Game
from wsim_core.models.orders import ShipOrders, TurnOrders
from wsim_core.serialization.scenario_loader import (
    ScenarioLoadError,
    initialize_game_from_scenario,
    load_scenario_from_file,
)

from ..store import get_game_store

router = APIRouter(prefix="/games", tags=["games"])

# Get the scenarios directory (relative to backend/)
SCENARIOS_DIR = Path(__file__).parent.parent.parent / "scenarios"


class CreateGameRequest(BaseModel):
    """Request to create a new game."""

    scenario_id: str = Field(description="Scenario ID to load")


class CreateGameResponse(BaseModel):
    """Response after creating a game."""

    game_id: str = Field(description="Unique game identifier")
    state: Game = Field(description="Initial game state")


class ScenarioInfo(BaseModel):
    """Information about an available scenario."""

    id: str = Field(description="Scenario ID")
    name: str = Field(description="Scenario name")
    description: str = Field(description="Scenario description")


@router.get("/scenarios", response_model=list[ScenarioInfo])
async def list_scenarios() -> list[ScenarioInfo]:
    """List all available scenarios.

    Returns:
        List of available scenarios with basic info

    Raises:
        HTTPException: If scenarios directory is not accessible
    """
    if not SCENARIOS_DIR.exists():
        raise HTTPException(status_code=500, detail="Scenarios directory not found")

    scenarios: list[ScenarioInfo] = []

    for scenario_file in SCENARIOS_DIR.glob("*.json"):
        try:
            scenario = load_scenario_from_file(scenario_file)
            scenarios.append(
                ScenarioInfo(
                    id=scenario.id,
                    name=scenario.name,
                    description=scenario.description,
                )
            )
        except ScenarioLoadError:
            # Skip invalid scenario files
            continue

    return scenarios


@router.post("", response_model=CreateGameResponse, status_code=201)
async def create_game(request: CreateGameRequest) -> CreateGameResponse:
    """Create a new game from a scenario.

    Args:
        request: Game creation request

    Returns:
        Created game with initial state

    Raises:
        HTTPException: If scenario not found or game creation fails
    """
    store = get_game_store()

    # Find scenario file
    scenario_file = SCENARIOS_DIR / f"{request.scenario_id}.json"
    if not scenario_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Scenario '{request.scenario_id}' not found",
        )

    # Load scenario
    try:
        scenario = load_scenario_from_file(scenario_file)
    except ScenarioLoadError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to load scenario: {e}",
        ) from e

    # Generate game ID and initialize game
    game_id = store.generate_game_id()
    game = initialize_game_from_scenario(scenario, game_id)

    # Store game
    try:
        store.create_game(game)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e

    return CreateGameResponse(game_id=game.id, state=game)


@router.get("/{game_id}", response_model=Game)
async def get_game(game_id: str) -> Game:
    """Get game state by ID.

    Args:
        game_id: The game identifier

    Returns:
        Current game state

    Raises:
        HTTPException: If game not found
    """
    store = get_game_store()
    game = store.get_game(game_id)

    if game is None:
        raise HTTPException(status_code=404, detail=f"Game '{game_id}' not found")

    return game


@router.delete("/{game_id}", status_code=204)
async def delete_game(game_id: str) -> None:
    """Delete a game.

    Args:
        game_id: The game identifier

    Raises:
        HTTPException: If game not found
    """
    store = get_game_store()

    try:
        store.delete_game(game_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


class SubmitOrdersRequest(BaseModel):
    """Request to submit movement orders for a turn."""

    side: str = Field(description="Player side (P1 or P2)", pattern="^(P1|P2)$")
    orders: list[ShipOrders] = Field(description="Orders for each ship")


class SubmitOrdersResponse(BaseModel):
    """Response after submitting orders."""

    state: Game = Field(description="Updated game state")
    orders_submitted: bool = Field(description="Whether orders were successfully submitted")


@router.post("/{game_id}/turns/{turn}/orders", response_model=SubmitOrdersResponse)
async def submit_orders(
    game_id: str, turn: int, request: SubmitOrdersRequest
) -> SubmitOrdersResponse:
    """Submit movement orders for a player's ships.

    Args:
        game_id: The game identifier
        turn: The turn number
        request: Orders submission request

    Returns:
        Updated game state with orders recorded

    Raises:
        HTTPException: If game not found, turn mismatch, or invalid phase
    """
    store = get_game_store()
    game = store.get_game(game_id)

    if game is None:
        raise HTTPException(status_code=404, detail=f"Game '{game_id}' not found")

    # Validate turn number
    if turn != game.turn_number:
        raise HTTPException(
            status_code=400,
            detail=f"Turn mismatch: expected {game.turn_number}, got {turn}",
        )

    # Validate phase
    if game.phase != GamePhase.PLANNING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit orders in phase {game.phase.value}",
        )

    # Validate that all orders are for ships belonging to this player
    player_ships = {ship.id for ship in game.get_ships_by_side(request.side)}
    order_ship_ids = {order.ship_id for order in request.orders}

    if not order_ship_ids.issubset(player_ships):
        invalid_ships = order_ship_ids - player_ships
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ship IDs for {request.side}: {invalid_ships}",
        )

    # Validate that all player's ships have orders
    if order_ship_ids != player_ships:
        missing_ships = player_ships - order_ship_ids
        raise HTTPException(
            status_code=400,
            detail=f"Missing orders for ships: {missing_ships}",
        )

    # Create TurnOrders
    turn_orders = TurnOrders(
        turn_number=turn,
        side=request.side,
        orders=request.orders,
        submitted=True,
    )

    # Store orders
    if request.side == "P1":
        game.p1_orders = turn_orders
    else:
        game.p2_orders = turn_orders

    # Update game in store
    store.update_game(game)

    return SubmitOrdersResponse(state=game, orders_submitted=True)


class MarkReadyRequest(BaseModel):
    """Request to mark a player as ready."""

    side: str = Field(description="Player side (P1 or P2)", pattern="^(P1|P2)$")


class MarkReadyResponse(BaseModel):
    """Response after marking ready."""

    state: Game = Field(description="Updated game state")
    ready: bool = Field(description="Whether the player is now ready")
    both_ready: bool = Field(description="Whether both players are ready")


@router.post("/{game_id}/turns/{turn}/ready", response_model=MarkReadyResponse)
async def mark_ready(game_id: str, turn: int, request: MarkReadyRequest) -> MarkReadyResponse:
    """Mark a player as ready to proceed.

    When both players are ready, orders are revealed.

    Args:
        game_id: The game identifier
        turn: The turn number
        request: Ready request

    Returns:
        Updated game state with ready status

    Raises:
        HTTPException: If game not found, turn mismatch, invalid phase, or orders not submitted
    """
    store = get_game_store()
    game = store.get_game(game_id)

    if game is None:
        raise HTTPException(status_code=404, detail=f"Game '{game_id}' not found")

    # Validate turn number
    if turn != game.turn_number:
        raise HTTPException(
            status_code=400,
            detail=f"Turn mismatch: expected {game.turn_number}, got {turn}",
        )

    # Validate phase
    if game.phase != GamePhase.PLANNING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot mark ready in phase {game.phase.value}",
        )

    # Validate that the player has submitted orders
    player_orders = game.p1_orders if request.side == "P1" else game.p2_orders
    if player_orders is None or not player_orders.submitted:
        raise HTTPException(
            status_code=400,
            detail=f"Player {request.side} has not submitted orders",
        )

    # Check if both players are ready (both have submitted orders)
    both_ready = (
        game.p1_orders is not None
        and game.p1_orders.submitted
        and game.p2_orders is not None
        and game.p2_orders.submitted
    )

    # Update game in store
    store.update_game(game)

    return MarkReadyResponse(state=game, ready=True, both_ready=both_ready)


class ResolveMovementResponse(BaseModel):
    """Response after resolving movement."""

    state: Game = Field(description="Updated game state with new ship positions")
    events: list[EventLogEntry] = Field(description="Event log entries for movement phase")


@router.post("/{game_id}/turns/{turn}/resolve/movement", response_model=ResolveMovementResponse)
async def resolve_movement(game_id: str, turn: int) -> ResolveMovementResponse:
    """Resolve simultaneous movement for all ships.

    This endpoint executes the movement phase including:
    1. Parse movement orders for all ships
    2. Execute simultaneous movement step-by-step
    3. Detect and resolve collisions
    4. Apply fouling to colliding ships
    5. Update drift tracking and apply drift
    6. Transition to COMBAT phase

    Args:
        game_id: The game identifier
        turn: The turn number

    Returns:
        Updated game state with new ship positions and movement events

    Raises:
        HTTPException: If game not found, turn mismatch, invalid phase, or movement fails
    """
    store = get_game_store()
    game = store.get_game(game_id)

    if game is None:
        raise HTTPException(status_code=404, detail=f"Game '{game_id}' not found")

    # Validate turn number
    if turn != game.turn_number:
        raise HTTPException(
            status_code=400,
            detail=f"Turn mismatch: expected {game.turn_number}, got {turn}",
        )

    # Validate phase
    if game.phase != GamePhase.PLANNING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resolve movement in phase {game.phase.value}",
        )

    # Validate that both players have submitted orders
    if game.p1_orders is None or not game.p1_orders.submitted:
        raise HTTPException(status_code=400, detail="Player P1 has not submitted orders")

    if game.p2_orders is None or not game.p2_orders.submitted:
        raise HTTPException(status_code=400, detail="Player P2 has not submitted orders")

    # Collect all movement events
    all_events: list[EventLogEntry] = []

    # Create RNG for this resolution (unseeded for normal play)
    rng = create_rng()

    # Parse movement orders for all ships
    parsed_movements = {}
    try:
        # Combine both players' orders
        all_orders = (game.p1_orders.orders if game.p1_orders else []) + (
            game.p2_orders.orders if game.p2_orders else []
        )

        for order in all_orders:
            ship = game.get_ship(order.ship_id)
            parsed = parse_movement(order.movement_string)
            validate_movement_within_allowance(parsed, ship.battle_sail_speed)
            parsed_movements[order.ship_id] = parsed

    except (KeyError, MovementParseError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid movement orders: {e}",
        ) from e

    # Execute simultaneous movement
    ships_before = game.ships.copy()
    try:
        updated_ships, movement_result = execute_simultaneous_movement(
            ships=game.ships,
            movements=parsed_movements,
            map_width=game.map_width,
            map_height=game.map_height,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Movement execution failed: {e}",
        ) from e

    # Create movement events
    for ship_id, bow_advanced in movement_result.ships_moved.items():
        ship = updated_ships[ship_id]
        all_events.append(
            EventLogEntry(
                turn_number=turn,
                phase=GamePhase.MOVEMENT,
                event_type="movement",
                summary=(
                    f"Ship {ship.name} executed movement: "
                    f"{parsed_movements[ship_id].original_notation}"
                ),
                metadata={
                    "ship_id": ship_id,
                    "ship_name": ship.name,
                    "movement_string": parsed_movements[ship_id].original_notation,
                    "bow_advanced": bow_advanced,
                    "final_position": {
                        "bow": {"col": ship.bow_hex.col, "row": ship.bow_hex.row},
                        "stern": {"col": ship.stern_hex.col, "row": ship.stern_hex.row},
                        "facing": ship.facing.value,
                    },
                },
            )
        )

    # Detect and resolve collisions
    resolved_ships, collision_result = detect_and_resolve_collisions(
        ships_before=ships_before,
        ships_after=updated_ships,
        rng=rng,
        turn_number=turn,
    )
    all_events.extend(collision_result.events)

    # Update drift tracking and apply drift
    drifted_ships, drift_result = check_and_apply_drift(
        ships=resolved_ships,
        movement_result=movement_result.ships_moved,
        wind_direction=game.wind_direction,
        map_width=game.map_width,
        map_height=game.map_height,
        turn_number=turn,
    )
    all_events.extend(drift_result.events)

    # Update game state
    game.ships = drifted_ships
    game.phase = GamePhase.COMBAT
    game.event_log.extend(all_events)

    # Update game in store
    store.update_game(game)

    return ResolveMovementResponse(state=game, events=all_events)


class FireBroadsideRequest(BaseModel):
    """Request to fire a ship's broadside."""

    ship_id: str = Field(description="ID of the ship firing")
    broadside: str = Field(description="Which broadside (L or R)", pattern="^(L|R)$")
    target_ship_id: str = Field(description="ID of the target ship")
    aim: str = Field(description="Aim point (hull or rigging)", pattern="^(hull|rigging)$")


class FireBroadsideResponse(BaseModel):
    """Response after firing a broadside."""

    state: Game = Field(description="Updated game state with damage applied")
    events: list[EventLogEntry] = Field(description="Combat event log entries")


@router.post("/{game_id}/turns/{turn}/combat/fire", response_model=FireBroadsideResponse)
async def fire_broadside(
    game_id: str, turn: int, request: FireBroadsideRequest
) -> FireBroadsideResponse:
    """Fire a ship's broadside at a target.

    This endpoint implements player-driven combat with the closest-target rule:
    1. Validates that the firing ship can fire (not struck, broadside loaded)
    2. Validates that the target is legal (closest enemy in arc)
    3. Resolves the broadside firing using hit tables
    4. Applies damage to the target ship
    5. Marks the broadside as empty (fired)
    6. Returns updated state and combat events

    Args:
        game_id: The game identifier
        turn: The turn number
        request: Firing request with ship, broadside, target, and aim

    Returns:
        Updated game state with damage applied and combat events

    Raises:
        HTTPException: If validation fails or firing is not legal
    """
    store = get_game_store()
    game = store.get_game(game_id)

    if game is None:
        raise HTTPException(status_code=404, detail=f"Game '{game_id}' not found")

    # Validate turn number
    if turn != game.turn_number:
        raise HTTPException(
            status_code=400,
            detail=f"Turn mismatch: expected {game.turn_number}, got {turn}",
        )

    # Validate phase
    if game.phase != GamePhase.COMBAT:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot fire in phase {game.phase.value}",
        )

    # Get firing ship
    try:
        firing_ship = game.get_ship(request.ship_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Ship '{request.ship_id}' not found") from e

    # Parse broadside and aim
    broadside = Broadside.L if request.broadside == "L" else Broadside.R
    aim = AimPoint.HULL if request.aim == "hull" else AimPoint.RIGGING

    # Validate that the broadside can fire
    if not can_fire_broadside(firing_ship, broadside):
        reasons = []
        if firing_ship.struck:
            reasons.append("ship has struck")
        load_state = firing_ship.load_L if broadside == Broadside.L else firing_ship.load_R
        if load_state == LoadState.EMPTY:
            reasons.append("broadside is not loaded")
        num_guns = firing_ship.guns_L if broadside == Broadside.L else firing_ship.guns_R
        if num_guns <= 0:
            reasons.append("no guns on this broadside")

        raise HTTPException(
            status_code=400,
            detail=f"Cannot fire broadside: {', '.join(reasons)}",
        )

    # Get legal targets using closest-target rule
    legal_targets = get_legal_targets(firing_ship, game.ships, broadside)

    if not legal_targets:
        raise HTTPException(
            status_code=400,
            detail="No legal targets in broadside arc",
        )

    # Validate that the requested target is legal
    target_ship_ids = {ship.id for ship in legal_targets}
    if request.target_ship_id not in target_ship_ids:
        legal_names = [ship.name for ship in legal_targets]
        raise HTTPException(
            status_code=400,
            detail=(
                f"Target '{request.target_ship_id}' is not a legal target. "
                f"Closest-target rule requires firing at one of: {', '.join(legal_names)}"
            ),
        )

    # Get target ship
    try:
        target_ship = game.get_ship(request.target_ship_id)
    except KeyError as e:
        raise HTTPException(
            status_code=404, detail=f"Target ship '{request.target_ship_id}' not found"
        ) from e

    # Get initial crew for firing ship (for crew quality modifier)
    # We need to load the scenario to get initial stats
    scenario_file = SCENARIOS_DIR / f"{game.scenario_id}.json"
    try:
        scenario = load_scenario_from_file(scenario_file)
        initial_crew = next(
            (s.crew for s in scenario.ships if s.id == firing_ship.id),
            firing_ship.crew,
        )
    except (ScenarioLoadError, StopIteration):
        # If we can't load scenario, use current crew as fallback
        initial_crew = firing_ship.crew

    # Create RNG and hit tables
    rng = create_rng()
    hit_tables = HitTables()

    # Resolve the broadside firing
    hit_result = resolve_broadside_fire(
        firing_ship=firing_ship,
        target_ship=target_ship,
        broadside=broadside,
        aim=aim,
        rng=rng,
        hit_tables=hit_tables,
        initial_crew=initial_crew,
    )

    # Apply damage to target ship
    apply_damage(target_ship, hit_result, aim, broadside)

    # Mark broadside as fired (empty)
    if broadside == Broadside.L:
        firing_ship.load_L = LoadState.EMPTY
    else:
        firing_ship.load_R = LoadState.EMPTY

    # Create combat event
    event = EventLogEntry(
        turn_number=turn,
        phase=GamePhase.COMBAT,
        event_type="broadside_fire",
        summary=(
            f"{firing_ship.name} fired {request.broadside} broadside at {target_ship.name} "
            f"(aiming at {aim.value}): {hit_result.hits} hits, "
            f"{hit_result.crew_casualties} crew casualties"
        ),
        metadata={
            "firing_ship_id": firing_ship.id,
            "firing_ship_name": firing_ship.name,
            "target_ship_id": target_ship.id,
            "target_ship_name": target_ship.name,
            "broadside": request.broadside,
            "aim": aim.value,
            "range": hit_result.range,
            "range_bracket": hit_result.range_bracket,
            "hits": hit_result.hits,
            "crew_casualties": hit_result.crew_casualties,
            "gun_damage": hit_result.gun_damage,
            "die_rolls": hit_result.die_rolls,
            "modifiers": hit_result.modifiers_applied,
            "target_state_after": {
                "hull": target_ship.hull,
                "rigging": target_ship.rigging,
                "crew": target_ship.crew,
                "guns_L": target_ship.guns_L,
                "guns_R": target_ship.guns_R,
                "struck": target_ship.struck,
            },
        },
    )

    # Update game state
    game.event_log.append(event)

    # Update game in store
    store.update_game(game)

    return FireBroadsideResponse(state=game, events=[event])


class BroadsideArcRequest(BaseModel):
    """Request for broadside arc and targeting information."""

    ship_id: str = Field(description="ID of the ship to get arc for")
    broadside: str = Field(description="Which broadside (L or R)", pattern="^(L|R)$")


class BroadsideArcResponse(BaseModel):
    """Response with broadside arc hexes and valid targets."""

    arc_hexes: list[tuple[int, int]] = Field(
        description="List of [col, row] hex coordinates in the broadside arc"
    )
    ships_in_arc: list[str] = Field(description="IDs of all ships with any part in arc")
    valid_targets: list[str] = Field(
        description="IDs of ships that can be legally targeted (closest enemies)"
    )
    closest_distance: int | None = Field(
        description="Distance to closest enemy, if any (for UI display)"
    )


@router.get(
    "/{game_id}/ships/{ship_id}/broadside/{broadside}/arc",
    response_model=BroadsideArcResponse,
)
async def get_broadside_arc_info(
    game_id: str, ship_id: str, broadside: str
) -> BroadsideArcResponse:
    """Get broadside arc hexes and valid target information.

    This endpoint provides visualization data for the UI to show:
    - Which hexes are in the broadside's firing arc
    - Which ships are in the arc
    - Which ships can be legally targeted (closest-target rule)

    Args:
        game_id: The game identifier
        ship_id: The ship whose broadside arc to calculate
        broadside: Which broadside (L or R)

    Returns:
        Arc hexes, ships in arc, and valid targets

    Raises:
        HTTPException: If game or ship not found, or invalid broadside
    """
    store = get_game_store()
    game = store.get_game(game_id)

    if game is None:
        raise HTTPException(status_code=404, detail=f"Game '{game_id}' not found")

    # Get ship
    try:
        ship = game.get_ship(ship_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Ship '{ship_id}' not found") from e

    # Parse broadside
    if broadside not in ("L", "R"):
        raise HTTPException(status_code=400, detail="Broadside must be 'L' or 'R'")

    broadside_enum = Broadside.L if broadside == "L" else Broadside.R

    # Get arc hexes
    arc_hexes_set = get_broadside_arc_hexes(ship, broadside_enum, max_range=10)
    arc_hexes_list: list[tuple[int, int]] = [
        (hex_coord.col, hex_coord.row) for hex_coord in arc_hexes_set
    ]

    # Get ships in arc
    all_ships = list(game.ships.values())
    ships_in_arc_info = get_ships_in_arc(ship, all_ships, broadside_enum, max_range=10)
    ships_in_arc_ids = [target_info.ship.id for target_info in ships_in_arc_info]

    # Get valid targets (enforcing closest-target rule)
    valid_targets_ships = get_all_valid_targets(ship, all_ships, broadside_enum, max_range=10)
    valid_target_ids = [target.id for target in valid_targets_ships]

    # Calculate closest distance for display
    closest_distance = None
    if ships_in_arc_info:
        # Only consider active enemies for closest distance
        enemy_distances = [
            target_info.distance
            for target_info in ships_in_arc_info
            if target_info.ship.side != ship.side and not target_info.ship.struck
        ]
        if enemy_distances:
            closest_distance = min(enemy_distances)

    return BroadsideArcResponse(
        arc_hexes=arc_hexes_list,
        ships_in_arc=ships_in_arc_ids,
        valid_targets=valid_target_ids,
        closest_distance=closest_distance,
    )


class ResolveReloadResponse(BaseModel):
    """Response after resolving reload phase."""

    state: Game = Field(description="Updated game state with reloaded broadsides")
    events: list[EventLogEntry] = Field(description="Reload event log entries")


@router.post("/{game_id}/turns/{turn}/resolve/reload", response_model=ResolveReloadResponse)
async def resolve_reload(game_id: str, turn: int) -> ResolveReloadResponse:
    """Reload all fired broadsides.

    This endpoint implements the reload phase:
    1. Reloads all empty broadsides on ships that can reload (not struck)
    2. Creates event log entries for reload operations
    3. Transitions game phase to RELOAD
    4. Returns updated game state and reload events

    Args:
        game_id: The game identifier
        turn: The turn number

    Returns:
        Updated game state with reloaded broadsides and reload events

    Raises:
        HTTPException: If game not found, turn mismatch, or invalid phase
    """
    store = get_game_store()
    game = store.get_game(game_id)

    if game is None:
        raise HTTPException(status_code=404, detail=f"Game '{game_id}' not found")

    # Validate turn number
    if turn != game.turn_number:
        raise HTTPException(
            status_code=400,
            detail=f"Turn mismatch: expected {game.turn_number}, got {turn}",
        )

    # Validate phase - reload can be called from COMBAT phase
    if game.phase != GamePhase.COMBAT:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reload in phase {game.phase.value}",
        )

    # Reload all ships
    ships_list = list(game.ships.values())
    reload_results = reload_all_ships(ships_list, turn)

    # Create reload events
    reload_events: list[EventLogEntry] = []
    for result in reload_results:
        ship = game.get_ship(result.ship_id)
        event = create_reload_event(result, turn, ship.name)
        reload_events.append(event)

    # Update game state
    game.phase = GamePhase.RELOAD
    game.event_log.extend(reload_events)

    # Update game in store
    store.update_game(game)

    return ResolveReloadResponse(state=game, events=reload_events)


class AdvanceTurnResponse(BaseModel):
    """Response after advancing to the next turn."""

    state: Game = Field(description="Updated game state in planning phase for new turn")


@router.post("/{game_id}/turns/{turn}/advance", response_model=AdvanceTurnResponse)
async def advance_turn(game_id: str, turn: int) -> AdvanceTurnResponse:
    """Advance to the next turn.

    This endpoint implements turn advancement:
    1. Validates that the current turn is complete (in RELOAD phase)
    2. Increments the turn number
    3. Clears orders for both players
    4. Transitions back to PLANNING phase
    5. Returns updated game state ready for next turn

    Args:
        game_id: The game identifier
        turn: The current turn number to advance from

    Returns:
        Updated game state in planning phase for new turn

    Raises:
        HTTPException: If game not found, turn mismatch, or invalid phase
    """
    store = get_game_store()
    game = store.get_game(game_id)

    if game is None:
        raise HTTPException(status_code=404, detail=f"Game '{game_id}' not found")

    # Validate turn number
    if turn != game.turn_number:
        raise HTTPException(
            status_code=400,
            detail=f"Turn mismatch: expected {game.turn_number}, got {turn}",
        )

    # Validate phase - can only advance from RELOAD phase
    if game.phase != GamePhase.RELOAD:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot advance turn from phase {game.phase.value}, must be in RELOAD phase",
        )

    # Increment turn number
    game.turn_number += 1

    # Clear orders for next turn
    game.p1_orders = None
    game.p2_orders = None

    # Return to planning phase
    game.phase = GamePhase.PLANNING

    # Update game in store
    store.update_game(game)

    return AdvanceTurnResponse(state=game)
