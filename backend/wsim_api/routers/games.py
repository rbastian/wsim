"""Game management API endpoints."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from wsim_core.models.common import GamePhase
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
