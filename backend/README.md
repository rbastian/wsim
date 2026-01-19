# WSIM Backend

Backend implementation for Wooden Ships & Iron Men digital game.

## Architecture

- `wsim_core`: Pure rules engine (UI-agnostic)
- `wsim_api`: FastAPI wrapper around core

## Development

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Type checking
uv run ty check wsim_core wsim_api tests

# Linting and formatting
uv run ruff check .
uv run ruff format .

# Run development server
uv run uvicorn wsim_api.main:app --reload
```

## Project Structure

```
backend/
  wsim_core/           # Core rules engine
    models/            # Pydantic models
    engine/            # Game logic
    tables/            # Data-driven rules
    events/            # Event logging
    serialization/     # State serialization
  wsim_api/            # FastAPI application
    routers/           # API endpoints
    deps/              # Dependency injection
  tests/               # Test suite
```
