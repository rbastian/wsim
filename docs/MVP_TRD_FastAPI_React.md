# Wooden Ships & Iron Men — Technical Requirements Document (TRD)
## MVP Option #2: FastAPI (Python) + ReactJS (Web UI)

**Project:** Digital Wooden Ships & Iron Men (WS&IM) MVP  
**Tech choice:** Python 3.12 backend + React frontend  
**Primary objective:** A correct, testable rules engine exposed via a clean API and playable via a modern web UI.

---

## 1) Goals

### MVP Goals
1. Implement a playable turn loop:
   - Scenario setup
   - Secret movement plotting
   - Simultaneous movement execution (including collisions + fouling)
   - Combat (broadsides + closest-target rule)
   - Reload
   - Turn advance + audit log
2. Build a web UI that supports:
   - Hotseat play (2 players on one browser) as the MVP baseline
   - Clear ship state visualization (board + ship log)
   - Order entry workflow + combat workflow
3. Ensure determinism and debuggability:
   - Seeded RNG option
   - Event log for all dice and rule outcomes
4. Maintain clean engineering standards:
   - Type safety
   - Strong model validation
   - High test coverage on rules engine

---

## 2) Non-Goals (MVP)

- Boarding parties / melee / capture
- Grappling / ungrappling
- Advanced rules (special ammo, wind shifts, repairs, etc.)
- Online multiplayer / matchmaking (beyond “hotseat”)
- Historical order-of-battle accuracy (scenario stats are test-balanced)

---

## 3) Technology Stack Requirements

### Backend
- **Language:** Python 3.12.x
- **Framework:** FastAPI
- **Data modeling:** Pydantic v2
- **Testing:** pytest
- **Type checking:** `ty` (Astral tool)
- **Formatting + linting:** ruff
- **Package management:** uv
- **ASGI server (dev/prod):** uvicorn

### Frontend
- **Framework:** ReactJS (TypeScript strongly recommended)
- **State management:** lightweight (React state + context) or Zustand
- **API client:** fetch or axios
- **Testing:** optional for MVP (Vitest), but not required to ship the first slice

### Optional (recommended)
- **pre-commit**: run ruff + ty + pytest locally
- **hypothesis**: property-based tests for engine invariants
- **OpenAPI**: FastAPI’s built-in OpenAPI used for API documentation

---

## 4) High-Level Architecture

### Core principle
The **rules engine is UI-agnostic** and does not depend on FastAPI, databases, or React.

**Backend layering:**
1. `wsim_core` (pure rules engine)
2. `wsim_api` (FastAPI wrapper around core)
3. `wsim_web` (React UI)

### Recommended repo layout
```
repo/
  backend/
    pyproject.toml
    wsim_core/
      __init__.py
      models/
      engine/
      tables/
      events/
      serialization/
    wsim_api/
      main.py
      routers/
      deps/
      settings.py
    tests/
  frontend/
    package.json
    src/
      api/
      components/
      pages/
      state/
      types/
```

---

## 5) Backend Requirements

## 5.1 Code quality standards
- ruff is mandatory for formatting and linting
- ty is mandatory for type checking
- pytest is mandatory for test suite
- no untyped “dict soup” passing between engine and API layer
- prefer `dataclasses` only if they interop cleanly with Pydantic models

## 5.2 Core rules engine requirements (`wsim_core`)
The engine must support the MVP phases:

### Phase: Scenario Setup
- Load scenario JSON
- Validate schema
- Initialize game state

### Phase: Planning
- Accept movement orders per ship per player
- Store orders privately until both players are ready
- Reveal orders after both submit

### Phase: Movement (Simultaneous)
- Parse movement strings
- Execute step-by-step movement simultaneously
- Apply drift rules
- Detect collisions and resolve outcomes
- Apply fouling state

### Phase: Combat
- Determine legal targets per broadside
- Enforce closest-target rule
- Resolve hits via data-driven tables
- Apply damage to hull/crew/guns/rigging
- Mark struck ships

### Phase: Reload
- Update broadside load state

### Phase: Turn Advance
- Increment turn number
- Persist event log

## 5.3 Deterministic RNG + event logging
### RNG requirements
- Engine must accept an injected RNG implementation
- Support:
  - unseeded “normal play”
  - seeded “test/replay mode”

### Event log requirements
- Every die roll produces an event entry:
  - roll type (d6, 2d6)
  - raw roll(s)
  - modifiers
  - outcome summary
- Every major rule resolution produces an event entry:
  - collision resolution
  - fouling result
  - firing resolution + hit result
  - damage application summary

---

## 6) API Requirements (FastAPI)

### 6.1 API principles
- API is a thin wrapper over engine calls
- API never re-implements game rules
- API returns:
  - updated `GameState`
  - `events` produced by the action
  - `errors` (if validation fails)

### 6.2 Session model (MVP)
For MVP, choose one:
- **In-memory game store** keyed by `game_id` (simplest)
- Optional file-backed persistence later

No database is required for MVP.

### 6.3 Endpoints (MVP)
#### Create game
- `POST /games`
- Request: `{ "scenario_id": "mvp_frigate_duel_v1" }`
- Response: `{ "game_id": "...", "state": {...} }`

#### Get game state
- `GET /games/{game_id}`
- Response: `{ "state": {...} }`

#### Submit orders (per player)
- `POST /games/{game_id}/turns/{turn}/orders`
- Request: `{ "player": "P1", "orders": [{ "ship_id": "...", "movement": "L1R1" }, ...] }`
- Response: `{ "state": {...}, "events": [...] }`

#### Mark player ready
- `POST /games/{game_id}/turns/{turn}/ready`
- Request: `{ "player": "P1" }`
- Response: `{ "state": {...} }`

#### Resolve movement
- `POST /games/{game_id}/turns/{turn}/resolve/movement`
- Response: `{ "state": {...}, "events": [...] }`

#### Resolve combat (MVP interactive)
Two approaches:

**A) Player-driven firing**
- `POST /games/{game_id}/turns/{turn}/combat/fire`
- Request: `{ "ship_id": "...", "broadside": "L", "target_ship_id": "...", "aim": "hull" }`
- Response: `{ "state": {...}, "events": [...] }`

**B) Auto-resolve combat**
- `POST /games/{game_id}/turns/{turn}/resolve/combat`
- Response: `{ "state": {...}, "events": [...] }`

MVP recommendation: **A)** (player-driven firing) because it matches tabletop decisions.

#### Reload
- `POST /games/{game_id}/turns/{turn}/resolve/reload`
- Response: `{ "state": {...}, "events": [...] }`

#### Advance turn
- `POST /games/{game_id}/turns/{turn}/advance`
- Response: `{ "state": {...} }`

### 6.4 CORS + local dev
- Enable CORS for `http://localhost:3000` (or Vite port)
- Expose OpenAPI docs at `/docs`

---

## 7) Frontend Requirements (React)

### 7.1 UI screens (MVP)
1. **Scenario Select / New Game**
   - list scenarios
   - create game button

2. **Game Screen**
   - Board view (hex map)
   - Ship inspector panel (log)
   - Orders panel
   - Combat panel
   - Event log panel

### 7.2 Board UI requirements
- Render hex grid (minimal styling)
- Render ships as 2-hex pieces with facing
- Click to select a ship
- Show overlays:
  - selected ship highlight
  - broadside arcs when in combat mode
  - legal targets highlight (only closest)

### 7.3 Orders UI requirements
- Per ship:
  - movement string input
  - basic validation feedback
- “Ready” button per player
- Prevent resolving movement until both players are ready

### 7.4 Combat UI requirements
- Select ship to fire
- Choose broadside L/R (only if loaded)
- Show legal targets list (filtered by closest-target rule)
- Choose aim: hull or rigging (if allowed)
- Fire action sends API request and renders updated state + events

### 7.5 Event log UI requirements
- Chronological list grouped by phase
- Each event displays:
  - action summary
  - dice roll(s)
  - modifiers
  - outcome

---

## 8) Scenario File Requirements

Scenario files must be loadable by backend and optionally displayed by frontend.

Minimum schema fields:
- `id`, `name`, `description`
- `map.width`, `map.height`
- `wind.direction`
- `turn_limit`
- `victory`
- `ships[]` with:
  - `id`, `side`, `name`
  - `battle_sail_speed`
  - `start.bow`, `start.facing`
  - `guns.L`, `guns.R`
  - `carronades.L`, `carronades.R`
  - `hull`, `rigging`, `crew`, `marines`
  - `marines`
  - `initial_load.L`, `initial_load.R`

---

## 9) Testing Requirements

### 9.1 Unit tests (must-have)
- Movement parser tests
- Movement execution tests
- Collision detection/resolution tests
- Closest-target selection tests
- Damage application tests
- Reload gating tests

### 9.2 Determinism tests (must-have)
- Given a fixed RNG seed and scenario:
  - movement resolution produces identical state + events
  - combat resolution produces identical state + events

### 9.3 Invariants (recommended)
- No ship overlaps after movement resolution
- No negative track values
- Unloaded broadside cannot fire
- Struck ships cannot fire

---

## 10) Performance & Operational Requirements

### MVP expectations
- Support at least 4 ships total on board (2v2)
- Target < 200ms per phase resolution locally
- No database required

### Logging
- Backend logs must include:
  - request id
  - game id
  - turn number
  - phase/action name
  - validation errors

---

## 11) Security Requirements (MVP)
- MVP assumes trusted local play
- Still required:
  - validate all inputs (Pydantic)
  - no arbitrary code execution
  - limit scenario file loading to known IDs (not raw filesystem paths)

---

## 12) Developer Workflow Requirements

### Local dev commands (conceptual)
Backend:
- `uv sync`
- `uv run uvicorn wsim_api.main:app --reload`

Frontend:
- `npm install`
- `npm run dev`

### CI checks (minimum)
- ruff format check
- ruff lint check
- ty type check
- pytest

---

## 13) MVP Milestones (suggested)

1. **Vertical Slice #1**
   - Load scenario
   - Render board
   - Select ship + view ship log

2. **Vertical Slice #2**
   - Enter orders + ready gate
   - Resolve movement and update board

3. **Vertical Slice #3**
   - Fire broadsides (closest-target enforcement)
   - Apply damage and show event log

4. **Vertical Slice #4**
   - Reload + advance turn
   - Repeat loop reliably

---

## 14) Open Questions
- Should combat be player-driven firing (recommended) or auto-resolved?
- Do we include “land” hexes in MVP for blocked fire testing?
- Do we store game state in-memory only, or add simple JSON persistence?
