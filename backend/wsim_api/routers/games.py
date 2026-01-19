"""Game management API endpoints."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from wsim_core.models.game import Game
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
