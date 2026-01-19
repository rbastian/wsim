# Wooden Ships & Iron Men — MVP PRD + Use Cases

**Source ruleset:** Wooden Ships & Iron Men (Tournament Edition Rules 2.6)  
**Scope:** Beginner-style core loop (plot orders → simultaneous movement → combat → reload)  
**MVP Goal:** Deliver a playable digital slice that feels like WS&IM and is good enough to validate the engine + UI.

---

## 1) Product Overview

### Summary
A digital implementation of *Wooden Ships & Iron Men* where players command sailing ships on a hex map. Each turn, players secretly plot movement orders, ships move simultaneously (including collisions/fouling), ships fire broadsides using the closest-target rule, damage is applied to ship logs, then broadsides reload.

### Why this MVP?
This MVP captures the “signature loop”:
- Secret plotting (simultaneous intent)
- Wind-influenced movement on a hex map
- Broadside arcs + closest-target restrictions
- Damage tracking on ship log sheets
- Repeatable turn resolution with auditability

---

## 2) Goals / Non-Goals

### Goals (MVP)
1. Support a full match loop with:
   - Scenario setup
   - Secret movement plotting
   - Simultaneous movement execution
   - Collision resolution + fouling status
   - Broadside firing and damage application
   - Reload
2. Enforce the core rules so outcomes are trustworthy.
3. Provide a readable “ship log” UI that reflects state clearly.
4. Provide an event log (dice + results) for transparency/debugging.

### Non-Goals (MVP)
- Grappling / ungrappling
- Boarding parties / melee / capture
- Advanced rules (special ammo, full sails, repairs, wind shifts, etc.)
- Historical accuracy in ship stats (we’ll use test-balanced values)
- Multiplayer networking (optional; MVP can be local hotseat)

---

## 3) MVP Turn Loop

MVP phases per turn:
1. **Planning** (secret orders)
2. **Movement** (simultaneous)
3. **Collision + Fouling** (during movement execution)
4. **Combat** (broadsides)
5. **Reload**
6. End turn → repeat

---

## 4) Core Concepts (MVP Data Model)

### Game
- `id`
- `scenario_id`
- `turn_number`
- `wind_direction`
- `phase`

### Ship
- Identity: `id`, `name`, `side`
- Position: `bow_hex`, `stern_hex`, `facing`
- Movement stats: `battle_sail_speed`
- Combat stats:
  - `guns_L`, `guns_R`
  - `carronades_L`, `carronades_R` (optional in MVP; can be 0)
- Tracks:
  - `hull`
  - `rigging`
  - `crew`
  - `marines`
- Load state:
  - `load_L`, `load_R` (Beginner: "R" roundshot only)
- Status flags:
  - `fouled` (true/false)
  - `struck` (true/false)

### Orders
- `turn_number`
- `ship_id`
- `movement_string` (e.g., `L1R1`, `0`)

### Event Log Entry
- `turn_number`, `phase`, `type`
- `dice_rolls`, `modifiers`
- `summary`
- optional `state_diff`

---

## 5) Use Cases (MVP)

### UC-MVP-01 — Create a game from a scenario
**Actor:** Host / Player  
**Goal:** Start a match with ships placed and initialized.

**Flow**
1. Select scenario
2. Load map + wind
3. Place ships (bow hex + facing)
4. Initialize ship logs

**Acceptance Criteria**
- Ships appear in correct starting positions
- All ship stats/tracks are initialized

---

### UC-MVP-02 — Secretly plot movement orders (Planning Phase)
**Actor:** Player  
**Goal:** Enter movement for each ship secretly.

**Flow**
1. Select ship
2. Enter movement notation (`0`, `L`, `R`, digits)
3. Repeat for all ships
4. Submit Ready
5. Reveal orders when both players are Ready

**Acceptance Criteria**
- Player cannot submit without orders for all ships
- Invalid syntax is rejected
- Opponent cannot see orders before both submit

---

### UC-MVP-03 — Execute simultaneous movement (Movement Phase)
**Actor:** Rules Engine  
**Goal:** Move all ships simultaneously.

**Flow**
1. Expand movement strings into step-by-step actions
2. Apply movement allowance rules
3. Execute simultaneous steps

**Acceptance Criteria**
- Ships end in valid positions
- Movement is deterministic given orders + dice (if any)

---

### UC-MVP-04 — Resolve drift
**Actor:** Rules Engine  
**Goal:** Apply drift when ships don’t advance bow hex for 2 turns.

**Flow**
1. Track consecutive turns with no bow movement
2. Drift 1 hex downwind when required

**Acceptance Criteria**
- Drift triggers at correct time
- Drift moves both bow and stern consistently

---

### UC-MVP-05 — Detect collisions and apply fouling
**Actor:** Rules Engine  
**Goal:** Resolve collisions and fouling status.

**Flow**
1. Detect collision during step replay
2. Determine which ship occupies collision hex
3. End voluntary movement for involved ships
4. Roll fouling and apply result

**Acceptance Criteria**
- No illegal overlapping ships
- Fouled status is applied and visible

---

### UC-MVP-06 — Fire broadsides (Combat Phase)
**Actor:** Player  
**Goal:** Fire loaded broadsides at legal targets.

**Flow**
1. Select ship
2. Choose broadside L/R
3. System shows legal target(s) (closest-target rule)
4. Choose target and aim (hull/rigging)
5. Resolve hits and apply damage

**Acceptance Criteria**
- Closest-target rule enforced
- Blocked fire (closest is friendly/land/etc.) enforced (land optional in MVP)
- Damage applied to correct track

---

### UC-MVP-07 — Reload broadsides (Reload Phase)
**Actor:** Player / Rules Engine  
**Goal:** Reload fired broadsides.

**Flow**
1. Fired broadsides become unloaded
2. Reload sets them to roundshot

**Acceptance Criteria**
- Cannot fire unloaded broadside
- After reload, broadside is available next turn

---

### UC-MVP-08 — End turn and advance
**Actor:** Rules Engine  
**Goal:** Advance turn counter and persist state.

**Flow**
1. Finalize event log
2. Increment turn
3. Return to Planning

**Acceptance Criteria**
- Turn count increments
- Ship state persists correctly

---

## 6) Functional Requirements

### FR-01 Scenario Loader
- Load scenario file
- Validate schema
- Instantiate map + ships + wind

### FR-02 Ship Log UI
- Display hull/rigging/crew/marines
- Display guns per broadside
- Display load state L/R
- Display fouled/struck status

### FR-03 Secret Orders UI
- Per-ship movement entry
- Ready/Submit gate
- Reveal after both ready

### FR-04 Movement Engine
- Parse movement notation
- Execute simultaneously step-by-step
- Enforce allowance constraints

### FR-05 Collision Engine
- Detect collision during step replay
- Resolve occupancy + stop movement
- Apply fouling result

### FR-06 Combat Engine
- Determine broadside arcs
- Enforce closest-target restriction
- Resolve hit tables (data-driven)
- Apply damage to tracks

### FR-07 Reload Engine
- Manage per-broadside load state

### FR-08 Event Log / Audit Trail
- Store dice results + modifiers + outcomes
- Replay turn results for debugging

---

## 7) MVP UX Requirements

### Board View
- Hex grid
- Ships as 2-hex pieces with facing indicator
- Highlight:
  - selected ship
  - planned path preview (optional)
  - legal firing arc and legal targets

### Ship Panel
- Ship name + side
- Hull / rigging / crew / marines
- Guns L/R and load state

### Orders Panel
- List ships with movement entry boxes
- Ready button

### Combat Panel
- Choose broadside L/R
- Choose target (from legal list)
- Fire button + dice results

---

## 8) MVP Acceptance Tests (Examples)

### Movement syntax
- Given a ship order `L1R1`
- When movement executes
- Then the ship turns left, moves 1, turns right, moves 1

### Collision resolution
- Given two ships enter the same hex on the same step
- When collision resolves
- Then only one ship occupies the hex and the other is moved back

### Closest-target firing
- Given two enemy ships in arc
- When firing a broadside
- Then only the closest enemy is a legal target

### Reload gating
- Given a broadside fired this turn
- When combat phase ends
- Then it is unloaded until reload phase completes

---

## 9) Risks / Notes

- Closest-target rule can confuse players unless the UI explains why targets are disabled.
- Simultaneous movement + collisions require careful step replay.
- Hit tables should be implemented as data, not hardcoded logic.

---

## 10) MVP Deliverables Checklist

- [ ] Scenario loader + 3 scenarios
- [ ] Ship + log state model
- [ ] Secret movement plotting UI
- [ ] Simultaneous movement engine
- [ ] Collision + fouling
- [ ] Broadside combat + damage
- [ ] Reload
- [ ] Turn log / audit trail
- [ ] Basic win/stop condition
