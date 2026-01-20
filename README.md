# Wooden Ships & Iron Men (WSIM) - Digital Implementation

A digital implementation of the classic naval combat board game *Wooden Ships & Iron Men*, where players command sailing ships in tactical Age of Sail battles. This MVP captures the signature game loop of secret movement plotting, simultaneous execution, broadside combat, and damage tracking.

## Table of Contents

- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [How to Play](#how-to-play)
- [Game Rules Summary](#game-rules-summary)
- [Running Tests](#running-tests)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

## Project Overview

This MVP implements the core game loop:

1. **Planning Phase** - Players secretly plot movement orders for their ships
2. **Movement Phase** - Ships move simultaneously according to plotted orders
3. **Combat Phase** - Ships fire broadsides at legal targets (closest-target rule)
4. **Reload Phase** - Fired broadsides are reloaded for the next turn

The game features:
- Hex-based tactical movement with wind mechanics
- Simultaneous turn resolution with collision detection and fouling
- Broadside arc targeting with closest-target restrictions
- Ship damage tracking (hull, rigging, crew, marines)
- Event logging for transparency and debugging
- Victory condition detection

### Implemented Features

- ✅ Scenario loading (3 MVP scenarios included)
- ✅ Secret movement plotting with ready gates
- ✅ Simultaneous movement execution
- ✅ Collision and fouling resolution
- ✅ Broadside combat with closest-target enforcement
- ✅ Damage tracking on ship logs
- ✅ Reload mechanics
- ✅ Victory condition detection
- ✅ Full turn loop with phase management
- ✅ Event log/audit trail
- ✅ Web UI with hex grid visualization
- ✅ Hotseat multiplayer (2 players on one browser)

### Not Implemented (Future)

- Grappling/ungrappling
- Boarding parties and melee combat
- Advanced rules (special ammo, wind shifts, repairs)
- Online multiplayer
- AI opponents

## Tech Stack

### Backend
- **Python 3.12+** - Core language
- **FastAPI** - Web framework
- **Pydantic v2** - Data validation and modeling
- **pytest** - Testing framework
- **ruff** - Linting and formatting
- **ty** - Type checking (Astral toolchain)
- **uv** - Package management
- **uvicorn** - ASGI server

### Frontend
- **React 19** - UI framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **ESLint** - Linting

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Node.js 20 or higher
- uv (Python package manager) - install from https://docs.astral.sh/uv/
- npm (comes with Node.js)

### Run the Game

1. Clone the repository:
```bash
git clone <repository-url>
cd wsim
```

2. Start the backend:
```bash
cd backend
uv sync --all-extras
uv run uvicorn wsim_api.main:app --reload
```
The API will be available at http://localhost:8000

3. Start the frontend (in a new terminal):
```bash
cd frontend
npm install
npm run dev
```
The UI will be available at http://localhost:5173

4. Open your browser and navigate to http://localhost:5173

## Development Setup

### Backend Setup

```bash
cd backend

# Install dependencies (including dev dependencies)
uv sync --all-extras

# Run the development server
uv run uvicorn wsim_api.main:app --reload

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=wsim_core --cov=wsim_api

# Type checking
uv run ty check wsim_core wsim_api tests

# Linting and formatting
uv run ruff check .
uv run ruff format .

# Fix linting issues automatically
uv run ruff check --fix .
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

### Pre-commit Hooks (Optional)

We provide optional pre-commit hooks for local quality gates:

```bash
# Install pre-commit (from project root)
pip install pre-commit

# Install the hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

See `.pre-commit-setup.md` for more details.

## How to Play

### Starting a Game

1. On the home page, you'll see a list of available scenarios
2. Click "Start Game" on any scenario to begin
3. The game will load with ships placed on the hex board

### Available Scenarios

1. **Frigate Duel** - Simple 1v1 frigate fight, great for learning
2. **Crossing Paths** - Multi-ship collision testing scenario (2v2)
3. **Two-Ship Line Battle** - Tests closest-target screening tactics (2v2)

### Turn Sequence

Each turn follows four phases:

#### 1. Planning Phase (Blue)

**For Player 1:**
- Click the "P1" button to select your side
- Enter movement orders for each of your ships
- Movement syntax (see Movement Controls below)
- Click "Submit Orders" when ready
- Click "Mark Ready" when you're satisfied with your orders

**For Player 2:**
- Click the "P2" button to select your side
- Enter movement orders for your ships
- Click "Submit Orders" when ready
- Click "Mark Ready" when satisfied

**Once both players are ready:**
- Click "Resolve Movement" to execute all movement simultaneously

#### 2. Movement Phase (Green)

- Ships move simultaneously according to their orders
- Collisions are detected and resolved automatically
- Fouling status is applied to colliding ships
- Phase automatically advances to Combat

#### 3. Combat Phase (Red)

**For each ship that can fire:**
- Select a ship from your ships list
- Choose which broadside to fire (L or R)
- The UI highlights the firing arc and legal targets
- Select a target (only closest enemies are legal)
- Choose aim point (Hull or Rigging)
- Click "Fire" to resolve the shot
- Damage is applied and shown in the event log

**After all desired shots:**
- Click "Reload Broadsides" to advance

#### 4. Reload Phase (Orange)

- All fired broadsides are reloaded with roundshot
- Click "Advance to Turn N" to start the next turn
- Game returns to Planning Phase

### Movement Controls

Movement is entered as a string of commands:

- `0` - Stay in place (drift check applies after 2 consecutive stationary turns)
- `L` - Turn 60° left
- `R` - Turn 60° right
- `1-9` - Move forward N hexes

**Examples:**
- `L1R1` - Turn left, move 1 hex forward, turn right, move 1 hex forward
- `2` - Move straight forward 2 hexes
- `LLR2` - Turn left twice, turn right once, move 2 hexes
- `0` - Stay in place

**Movement Allowance:**
- Each ship has a battle sail speed (typically 3-4)
- You can't move more hexes than your speed per turn
- Turning does not cost movement

### Combat Controls

**Broadside Arc:**
- Each side of the ship (L/R) can fire
- Broadsides fire perpendicular to the ship's facing
- Maximum range varies (typically 5-8 hexes)
- Arc is highlighted when selecting a broadside

**Closest-Target Rule:**
- You can ONLY fire at the closest enemy in arc
- If a friendly ship is closer, you cannot fire
- This creates tactical screening opportunities

**Aim Points:**
- **Hull** - Damages hull and may destroy guns
- **Rigging** - Damages rigging (reduces speed)

**Damage:**
- Each hit rolls on damage tables
- Damage is applied to ship tracks
- Ships with 0 hull strike their colors (surrender)
- Struck ships are removed from play

### Victory Conditions

Victory conditions vary by scenario:
- **First Struck** - First side to have a ship struck loses
- **Score After Turns** - Most hull remaining after turn limit
- **First Side Struck Two Ships** - First side to lose 2 ships loses

The game will announce the winner when victory conditions are met.

## Game Rules Summary

This is a simplified summary. For complete rules, see the Tournament Edition Rules 2.6.

### Core Concepts

**Ships:**
- Occupy 2 hexes (bow and stern)
- Have facing (6 directions: N, NE, SE, S, SW, NW)
- Have tracks: Hull, Rigging, Crew, Marines
- Have guns on left and right broadsides
- Have load state per broadside (Loaded/Unloaded)

**Wind:**
- Fixed direction for entire scenario
- Affects movement allowance (not yet implemented in MVP)
- Causes drift for stationary ships

**Phases:**
1. Planning - Secret order entry
2. Movement - Simultaneous execution
3. Combat - Sequential broadside firing
4. Reload - Restore fired broadsides

### Movement Rules

- Ships move simultaneously in discrete steps
- Each action in movement string is executed in order
- Collisions stop further voluntary movement
- Ships that don't move their bow for 2 consecutive turns drift 1 hex downwind

### Combat Rules

- Only loaded broadsides can fire
- Can only fire at enemies in broadside arc
- Must fire at closest enemy in arc
- Roll on hit tables (data-driven)
- Damage applied to appropriate track
- Ships with 0 hull strike colors

### Fouling

- When ships collide, they may become fouled
- Fouled ships have restricted movement
- Unfouling not implemented in MVP

## Running Tests

### Backend Tests

```bash
cd backend

# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=wsim_core --cov=wsim_api --cov-report=html

# Run specific test file
uv run pytest tests/engine/test_movement_parser.py

# Run tests matching pattern
uv run pytest -k "test_movement"
```

### Test Coverage

The backend has comprehensive test coverage (356 tests) covering:

- Movement parsing and validation
- Movement execution and simultaneous resolution
- Collision detection and resolution
- Broadside arc calculation
- Targeting and closest-target enforcement
- Combat resolution and damage application
- Victory condition detection
- Drift mechanics
- Fouling status
- Event logging
- Scenario loading
- End-to-end integration scenarios

### Frontend Tests

Frontend testing is optional for MVP. To add tests:

```bash
cd frontend
npm install --save-dev vitest
# Configure vitest in vite.config.ts
```

## API Documentation

### Interactive API Docs

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Scenarios

```
GET /games/scenarios
```
List all available scenarios

#### Game Management

```
POST /games
Body: { "scenario_id": "mvp_frigate_duel_v1" }
```
Create a new game from a scenario

```
GET /games/{game_id}
```
Get current game state

#### Turn Management

```
POST /games/{game_id}/turns/{turn}/orders
Body: { "player": "P1", "orders": [...] }
```
Submit movement orders for a player

```
POST /games/{game_id}/turns/{turn}/ready
Body: { "player": "P1" }
```
Mark player ready to proceed

```
POST /games/{game_id}/turns/{turn}/resolve/movement
```
Execute simultaneous movement (both players must be ready)

#### Combat

```
POST /games/{game_id}/turns/{turn}/combat/fire
Body: { "ship_id": "...", "broadside": "L", "target_ship_id": "...", "aim": "hull" }
```
Fire a broadside at a target

```
POST /games/{game_id}/turns/{turn}/combat/targets
Body: { "ship_id": "...", "broadside": "L" }
```
Get legal targets for a broadside

```
POST /games/{game_id}/turns/{turn}/resolve/reload
```
Reload all fired broadsides

#### Turn Advance

```
POST /games/{game_id}/turns/{turn}/advance
```
Advance to next turn

## Project Structure

```
wsim/
├── backend/                    # Python backend
│   ├── wsim_core/             # Pure rules engine (UI-agnostic)
│   │   ├── models/            # Pydantic data models
│   │   │   ├── common.py      # Enums and shared types
│   │   │   ├── game.py        # Game state model
│   │   │   ├── orders.py      # Order models
│   │   │   ├── events.py      # Event log models
│   │   │   └── ship.py        # Ship model
│   │   ├── engine/            # Game logic
│   │   │   ├── movement_parser.py        # Parse movement strings
│   │   │   ├── movement_executor.py      # Execute movement
│   │   │   ├── collision.py              # Collision detection
│   │   │   ├── arc.py                    # Broadside arc calculation
│   │   │   ├── targeting.py              # Target selection
│   │   │   ├── combat.py                 # Combat resolution
│   │   │   ├── drift.py                  # Drift mechanics
│   │   │   ├── reload.py                 # Reload logic
│   │   │   ├── victory.py                # Victory detection
│   │   │   └── rng.py                    # RNG abstraction
│   │   ├── tables/            # Data-driven hit tables
│   │   │   └── hit_tables.py
│   │   ├── events/            # Event creation utilities
│   │   │   └── event_factory.py
│   │   └── serialization/     # Scenario loading
│   │       └── scenario_loader.py
│   ├── wsim_api/              # FastAPI application
│   │   ├── main.py            # App entry point
│   │   ├── store.py           # In-memory game storage
│   │   ├── routers/           # API endpoints
│   │   │   └── games.py       # Game management routes
│   │   └── deps/              # Dependency injection
│   │       └── __init__.py
│   ├── tests/                 # Test suite
│   │   ├── engine/            # Engine unit tests
│   │   ├── api/               # API integration tests
│   │   └── integration/       # End-to-end tests
│   ├── scenarios/             # Scenario JSON files
│   │   ├── mvp_frigate_duel_v1.json
│   │   ├── mvp_crossing_paths_v1.json
│   │   └── mvp_two_ship_line_battle_v1.json
│   ├── pyproject.toml         # Python dependencies
│   └── uv.lock               # Lock file
│
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── main.tsx          # App entry point
│   │   ├── App.tsx           # Root component with routing
│   │   ├── api/              # API client functions
│   │   │   └── client.ts
│   │   ├── types/            # TypeScript types
│   │   │   └── game.ts
│   │   ├── components/       # React components
│   │   │   ├── HexGrid.tsx              # Hex board visualization
│   │   │   ├── Ship.tsx                 # Ship rendering
│   │   │   ├── ShipLogPanel.tsx         # Ship status display
│   │   │   ├── OrdersPanel.tsx          # Movement order entry
│   │   │   ├── CombatPanel.tsx          # Combat actions
│   │   │   ├── PhaseControlPanel.tsx    # Phase management
│   │   │   └── EventLog.tsx             # Event history
│   │   ├── pages/            # Page components
│   │   │   ├── HomePage.tsx             # Scenario selection
│   │   │   └── GamePage.tsx             # Main game screen
│   │   └── assets/           # Static assets
│   ├── package.json          # Node dependencies
│   └── tsconfig.json         # TypeScript config
│
├── docs/                      # Documentation
│   ├── MVP_PRD_and_Use_Cases.md         # Product requirements
│   ├── MVP_Scenarios.md                 # Scenario definitions
│   └── MVP_TRD_FastAPI_React.md         # Technical requirements
│
├── .github/
│   └── workflows/
│       └── ci.yml            # CI/CD pipeline
│
├── .beads/                   # Issue tracking (beads)
├── CLAUDE.md                 # Instructions for Claude Code
├── progress.txt              # Development progress log
└── README.md                 # This file
```

## Contributing

### Code Quality Standards

All code must pass:
- **Backend**: ruff format, ruff lint, ty type check, pytest
- **Frontend**: TypeScript type-check, ESLint

These are enforced by CI on all pull requests.

### Development Workflow

1. Check available tasks with `bd ready`
2. Pick a task and create a feature branch: `git checkout -b feature/wsim-<id>-<description>`
3. Update issue status: `bd update <id> --status in_progress`
4. Make your changes
5. Run quality checks (see Development Setup above)
6. Commit with issue ID: `git commit -m "Description (wsim-<id>)"`
7. Push and create PR: `gh pr create --title "Title (wsim-<id>)" --body "..."`
8. Update issue: `bd close <id> --reason "Completed"`
9. Sync beads: `bd sync`

### Running CI Locally

```bash
# Backend checks
cd backend
uv run ruff format --check .
uv run ruff check .
uv run ty check wsim_core wsim_api tests
uv run pytest

# Frontend checks
cd frontend
npm run type-check
npm run lint
npm run build
```

### Issue Tracking

This project uses **beads** for issue tracking:

```bash
# Find work
bd ready

# View issue
bd show <id>

# Update status
bd update <id> --status in_progress
bd update <id> --notes "Progress update"

# Close issue
bd close <id> --reason "Done"

# Sync with git
bd sync
```

## License

[Add license information here]

## Credits

Based on the board game *Wooden Ships & Iron Men* (Tournament Edition Rules 2.6).

---

**Status**: MVP Complete - All core features implemented and tested. Ready for play!
