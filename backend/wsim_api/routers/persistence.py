"""Game persistence management API endpoints.

Provides manual save/load operations for games.
Only available when using persistent store.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..persistent_store import PersistentGameStore
from ..store import GameStore, get_game_store

router = APIRouter(prefix="/persistence", tags=["persistence"])


class SaveGameResponse(BaseModel):
    """Response after saving a game."""

    game_id: str = Field(description="Game ID that was saved")
    file_path: str = Field(description="Path to saved file")


class SaveAllResponse(BaseModel):
    """Response after saving all games."""

    count: int = Field(description="Number of games saved")
    game_ids: list[str] = Field(description="List of saved game IDs")


class ListSavedResponse(BaseModel):
    """Response listing saved games."""

    count: int = Field(description="Number of saved games")
    game_ids: list[str] = Field(description="List of saved game IDs")


class LoadGameResponse(BaseModel):
    """Response after loading a game."""

    game_id: str = Field(description="Game ID that was loaded")
    success: bool = Field(description="Whether load was successful")


class ClearSavedResponse(BaseModel):
    """Response after clearing saved games."""

    count: int = Field(description="Number of files deleted")


def _get_persistent_store() -> PersistentGameStore:
    """Get persistent store or raise error if not available.

    Returns:
        The persistent game store

    Raises:
        HTTPException: If persistence is not enabled
    """
    store = get_game_store()
    if not isinstance(store, PersistentGameStore):
        raise HTTPException(
            status_code=503,
            detail="Persistence not enabled. Server must be configured with persistent store.",
        )
    return store


@router.post("/games/{game_id}/save", response_model=SaveGameResponse)
async def save_game(game_id: str) -> SaveGameResponse:
    """Manually save a specific game to disk.

    Normally games are auto-saved when using persistent store.
    This endpoint allows explicit save operations.

    Args:
        game_id: Game to save

    Returns:
        Save confirmation with file path

    Raises:
        HTTPException: If game not found or persistence not enabled
    """
    store = _get_persistent_store()

    game = store.get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

    file_path = store._persistence.save_game(game)

    return SaveGameResponse(game_id=game_id, file_path=str(file_path))


@router.post("/games/{game_id}/load", response_model=LoadGameResponse)
async def load_game(game_id: str) -> LoadGameResponse:
    """Load a game from disk into memory.

    Useful for restoring games after server restart.

    Args:
        game_id: Game to load

    Returns:
        Load confirmation

    Raises:
        HTTPException: If game file not found or invalid, or persistence not enabled
    """
    store = _get_persistent_store()

    try:
        game = store._persistence.load_game(game_id)
        # Add to in-memory store using parent method to avoid re-saving
        GameStore.create_game(store, game)
        return LoadGameResponse(game_id=game_id, success=True)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Saved game {game_id} not found") from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid game file: {e}") from e


@router.post("/save-all", response_model=SaveAllResponse)
async def save_all_games() -> SaveAllResponse:
    """Save all in-memory games to disk.

    Useful for ensuring all games are persisted.

    Returns:
        Count and list of saved games

    Raises:
        HTTPException: If persistence not enabled
    """
    store = _get_persistent_store()

    games = store.list_games()
    count = store.save_all()

    return SaveAllResponse(count=count, game_ids=[g.id for g in games])


@router.get("/saved-games", response_model=ListSavedResponse)
async def list_saved_games() -> ListSavedResponse:
    """List all games that have saved files on disk.

    Returns:
        Count and list of saved game IDs

    Raises:
        HTTPException: If persistence not enabled
    """
    store = _get_persistent_store()

    game_ids = store._persistence.list_saved_games()

    return ListSavedResponse(count=len(game_ids), game_ids=game_ids)


@router.delete("/saved-games", response_model=ClearSavedResponse)
async def clear_saved_games() -> ClearSavedResponse:
    """Delete all saved game files from disk.

    Does NOT affect in-memory games.
    Use with caution - this cannot be undone.

    Returns:
        Number of files deleted

    Raises:
        HTTPException: If persistence not enabled
    """
    store = _get_persistent_store()

    count = store.clear_saved_files()

    return ClearSavedResponse(count=count)


@router.delete("/games/{game_id}/saved", response_model=dict[str, str])
async def delete_saved_game(game_id: str) -> dict[str, str]:
    """Delete a specific saved game file from disk.

    Does NOT affect in-memory game if loaded.

    Args:
        game_id: Game file to delete

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If game file not found or persistence not enabled
    """
    store = _get_persistent_store()

    try:
        store._persistence.delete_saved_game(game_id)
        return {"message": f"Saved game {game_id} deleted", "game_id": game_id}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Saved game {game_id} not found") from e
