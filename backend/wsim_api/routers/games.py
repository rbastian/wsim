"""Game management API endpoints."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from wsim_core.engine.collision import detect_and_resolve_collisions
from wsim_core.engine.drift import check_and_apply_drift
from wsim_core.engine.movement_executor import execute_simultaneous_movement
from wsim_core.engine.movement_parser import (
    MovementParseError,
    parse_movement,
    validate_movement_within_allowance,
)
from wsim_core.engine.rng import create_rng
from wsim_core.models.common import GamePhase
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
