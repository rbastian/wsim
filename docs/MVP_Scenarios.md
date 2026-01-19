# Wooden Ships & Iron Men — MVP Scenarios (Draft)

These scenarios are **engine-validation scenarios** (not historical).  
They are designed to progressively exercise MVP systems:
1) movement + combat
2) collision + fouling
3) multi-ship targeting (closest-target screening)

---

## Scenario 1 — Frigate Duel (Baseline)

**Purpose**
- Test secret plotting, wind-relative movement, broadside arcs, reload, damage tracking.
- Minimal chaos; good for first playable demo.

```json
{
  "id": "mvp_frigate_duel_v1",
  "name": "Frigate Duel",
  "description": "A simple 1v1 frigate fight. Great for learning movement and broadsides.",
  "map": { "width": 25, "height": 20 },
  "wind": { "direction": "W" },
  "turn_limit": 20,
  "victory": { "type": "first_struck" },
  "ships": [
    {
      "id": "p1_frigate_1",
      "side": "P1",
      "name": "HMS Swift",
      "battle_sail_speed": 4,
      "start": { "bow": [5, 10], "facing": "E" },
      "guns": { "L": 10, "R": 10 },
      "carronades": { "L": 0, "R": 0 },
      "hull": 12,
      "rigging": 10,
      "crew": 10,
      "marines": 2,
      "initial_load": { "L": "R", "R": "R" }
    },
    {
      "id": "p2_frigate_1",
      "side": "P2",
      "name": "FS Vengeur",
      "battle_sail_speed": 4,
      "start": { "bow": [19, 10], "facing": "W" },
      "guns": { "L": 10, "R": 10 },
      "carronades": { "L": 0, "R": 0 },
      "hull": 12,
      "rigging": 10,
      "crew": 10,
      "marines": 2,
      "initial_load": { "L": "R", "R": "R" }
    }
  ]
}
```

---

## Scenario 2 — Crossing Paths (Collision + Fouling Test)

**Purpose**
- Stress-test simultaneous movement replay.
- Validate collision resolution, movement truncation, and fouling status.

```json
{
  "id": "mvp_crossing_paths_v1",
  "name": "Crossing Paths",
  "description": "Ships start close and on converging courses. Expect collisions and fouling.",
  "map": { "width": 18, "height": 14 },
  "wind": { "direction": "S" },
  "turn_limit": 12,
  "victory": { "type": "score_after_turns", "metric": "remaining_hull" },
  "ships": [
    {
      "id": "p1_sloop_1",
      "side": "P1",
      "name": "P1 Sloop A",
      "battle_sail_speed": 3,
      "start": { "bow": [6, 6], "facing": "E" },
      "guns": { "L": 6, "R": 6 },
      "carronades": { "L": 0, "R": 0 },
      "hull": 8,
      "rigging": 8,
      "crew": 8,
      "marines": 1,
      "initial_load": { "L": "R", "R": "R" }
    },
    {
      "id": "p1_sloop_2",
      "side": "P1",
      "name": "P1 Sloop B",
      "battle_sail_speed": 3,
      "start": { "bow": [6, 8], "facing": "E" },
      "guns": { "L": 6, "R": 6 },
      "carronades": { "L": 0, "R": 0 },
      "hull": 8,
      "rigging": 8,
      "crew": 8,
      "marines": 1,
      "initial_load": { "L": "R", "R": "R" }
    },
    {
      "id": "p2_sloop_1",
      "side": "P2",
      "name": "P2 Sloop A",
      "battle_sail_speed": 3,
      "start": { "bow": [11, 7], "facing": "W" },
      "guns": { "L": 6, "R": 6 },
      "carronades": { "L": 0, "R": 0 },
      "hull": 8,
      "rigging": 8,
      "crew": 8,
      "marines": 1,
      "initial_load": { "L": "R", "R": "R" }
    },
    {
      "id": "p2_sloop_2",
      "side": "P2",
      "name": "P2 Sloop B",
      "battle_sail_speed": 3,
      "start": { "bow": [11, 9], "facing": "W" },
      "guns": { "L": 6, "R": 6 },
      "carronades": { "L": 0, "R": 0 },
      "hull": 8,
      "rigging": 8,
      "crew": 8,
      "marines": 1,
      "initial_load": { "L": "R", "R": "R" }
    }
  ]
}
```

---

## Scenario 3 — Two-Ship Line Battle (Closest-Target + Screening)

**Purpose**
- Validate multi-ship interactions:
  - closest-target restriction
  - “screening” tactics (small ship blocks firing at larger ship)
- Still small enough for MVP UI.

```json
{
  "id": "mvp_two_ship_line_battle_v1",
  "name": "Two-Ship Line Battle",
  "description": "Two ships per side. Positioning matters because the closest-target rule can block shots.",
  "map": { "width": 28, "height": 18 },
  "wind": { "direction": "W" },
  "turn_limit": 18,
  "victory": { "type": "first_side_struck_two_ships" },
  "ships": [
    {
      "id": "p1_frigate_1",
      "side": "P1",
      "name": "HMS Arrow",
      "battle_sail_speed": 4,
      "start": { "bow": [6, 7], "facing": "E" },
      "guns": { "L": 10, "R": 10 },
      "carronades": { "L": 0, "R": 0 },
      "hull": 12,
      "rigging": 10,
      "crew": 10,
      "marines": 2,
      "initial_load": { "L": "R", "R": "R" }
    },
    {
      "id": "p1_brig_1",
      "side": "P1",
      "name": "HMS Kite",
      "battle_sail_speed": 3,
      "start": { "bow": [6, 11], "facing": "E" },
      "guns": { "L": 7, "R": 7 },
      "carronades": { "L": 0, "R": 0 },
      "hull": 10,
      "rigging": 9,
      "crew": 9,
      "marines": 1,
      "initial_load": { "L": "R", "R": "R" }
    },
    {
      "id": "p2_frigate_1",
      "side": "P2",
      "name": "FS Tempete",
      "battle_sail_speed": 4,
      "start": { "bow": [21, 7], "facing": "W" },
      "guns": { "L": 10, "R": 10 },
      "carronades": { "L": 0, "R": 0 },
      "hull": 12,
      "rigging": 10,
      "crew": 10,
      "marines": 2,
      "initial_load": { "L": "R", "R": "R" }
    },
    {
      "id": "p2_brig_1",
      "side": "P2",
      "name": "FS Mouche",
      "battle_sail_speed": 3,
      "start": { "bow": [21, 11], "facing": "W" },
      "guns": { "L": 7, "R": 7 },
      "carronades": { "L": 0, "R": 0 },
      "hull": 10,
      "rigging": 9,
      "crew": 9,
      "marines": 1,
      "initial_load": { "L": "R", "R": "R" }
    }
  ]
}
```
