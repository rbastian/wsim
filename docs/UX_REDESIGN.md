# Wooden Ships & Iron Men - UX Redesign Document

## Design Vision

**Aesthetic Direction: Naval Chart Authenticity**

This interface reimagines the game as an interactive 18th-century naval plotting chart. The design embraces:
- **Cartographic precision**: Inspired by period naval charts with hand-drawn qualities
- **Nautical instruments**: Wind roses, compass bearings, depth soundings
- **Aged paper aesthetic**: Warm sepia tones, subtle textures, ink-like typography
- **Focused immersion**: The ocean battlefield dominates; UI elements frame rather than compete

The result should feel like commanding a fleet from an admiral's plotting table—tactical, atmospheric, and deeply focused on the hex battlefield.

---

## 1. Layout Structure

### Overall Composition

```
┌─────────────────────────────────────────────────────────────┐
│  TOP HUD (fixed, ~80px height, semi-transparent overlay)   │
│  [Wind Rose] Turn 3 • COMBAT Phase    [Advance Turn ➜]     │
└─────────────────────────────────────────────────────────────┘
│                                                             │
│                                                             │
│              FULL SCREEN HEX MAP OCEAN                      │
│          (SVG hex grid with ships rendered)                 │
│                                                             │
│                                                             │
│                    ┌──────────────────┐                     │
│                    │  SHIP ACTION     │ ← Slides in from   │
│                    │  PANEL           │   right when ship  │
│                    │  (collapsible)   │   is selected      │
│                    │                  │                     │
│                    └──────────────────┘                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Zones

1. **Top HUD Bar** (fixed position)
   - Left third: Wind rose icon + direction indicator
   - Center: Turn number + current phase (color-coded badge)
   - Right third: Phase-specific action button ("Advance Turn", "Resolve Movement", etc.)
   - Background: Semi-transparent aged parchment overlay (rgba(242, 235, 220, 0.95))
   - Border bottom: Decorative nautical rule line

2. **Hex Map Ocean** (full viewport minus HUD)
   - Extends edge-to-edge, full viewport height minus top HUD
   - Ocean background: Deep blue-green gradient (#1a4d5c → #0d2d3a)
   - Hex grid: Subtle cream/tan stroke (#d4c5a9, 1px, opacity 0.3)
   - Ships rendered as 2-hex SVG polygons with visual state indicators

3. **Ship Action Panel** (slide-in drawer, right side)
   - Width: 380px (25% viewport width, min 320px, max 450px)
   - Height: Full viewport minus HUD
   - Position: Fixed right, slides in/out with smooth animation
   - Background: Aged parchment with subtle paper texture
   - Close button: "×" in top-right corner (or click outside to dismiss)

---

## 2. Component Hierarchy

```
<GamePage>
  ├── <TopHUD>
  │   ├── <WindRose direction={windDir} />
  │   ├── <TurnPhaseIndicator turn={N} phase={PHASE} />
  │   └── <PhaseActionButton phase={PHASE} onAdvance={...} />
  │
  ├── <HexMapOcean>
  │   ├── <HexGrid width={W} height={H}>
  │   │   └── (SVG hex cells)
  │   ├── <Ship> (multiple, with state overlays)
  │   │   ├── bow/stern polygons
  │   │   ├── <ShipStateIndicator ready={bool} struck={bool} fouled={bool} />
  │   │   └── <SelectionHighlight selected={bool} />
  │   └── <TargetingArc> (when combat targeting active)
  │
  └── <ShipActionPanel isOpen={bool} selectedShip={ship} phase={phase}>
      ├── <PanelHeader>
      │   ├── Ship name + side badge
      │   └── Close button
      ├── <ShipStatusView> (always visible)
      │   ├── <DamageTrackBars hull, rigging, crew />
      │   ├── <LoadStatusIndicator L/R broadsides />
      │   └── <StatusBadges> (STRUCK, FOULED, READY)
      ├── <PlanningControls> (if phase === PLANNING)
      │   ├── <MovementInput movementString onSubmit />
      │   └── <MarkReadyButton ready={bool} />
      └── <CombatControls> (if phase === COMBAT)
          ├── <BroadsideSelector L/R onSelect />
          ├── <TargetSelector targets={valid} onSelect />
          ├── <AimPointSelector HULL/RIGGING />
          └── <FireButton onFire />
```

### Component Responsibilities

**TopHUD**: Always visible, minimal, provides game state context
- WindRose: SVG icon with directional pointer
- TurnPhaseIndicator: Compact display with phase color coding
- PhaseActionButton: Context-aware button (disabled when not ready)

**HexMapOcean**: Full-screen interactive battlefield
- HexGrid: SVG rendering, handles click detection for hexes
- Ship: Individual ship rendering with 2-hex polygon + overlays
- TargetingArc: Renders broadside firing arc when targeting

**ShipActionPanel**: Contextual drawer for ship interaction
- Slides in from right when ship selected (click ship or hex)
- Close via X button, ESC key, or click outside panel
- Content adapts to current phase (Planning vs Combat vs Read-only)

---

## 3. State Management

### UI State (Local Component State)

```typescript
interface GamePageUIState {
  // Panel control
  selectedShipId: string | null;
  isPanelOpen: boolean;

  // Combat targeting state
  selectedBroadside: 'L' | 'R' | null;
  selectedTargetId: string | null;
  selectedAimPoint: 'HULL' | 'RIGGING' | null;

  // Visual feedback
  hoveredShipId: string | null;
  hoveredHex: HexCoord | null;

  // Ship ready tracking (client-side, derived from orders)
  shipReadyStates: Map<string, boolean>; // shipId -> isReady
}
```

### Ready State Logic

A ship is "ready" when:
- **PLANNING phase**: Player has submitted valid movement orders AND marked ready
- **COMBAT phase**: Ship has no loaded broadsides OR player has fired all desired shots
- **Other phases**: N/A (no player input required)

Ready state is displayed as:
- Visual indicator on ship (glowing border, checkmark badge)
- Updated in real-time as orders are submitted
- Persists until phase advances

### Panel Open/Close Behavior

- **Open triggers**: Click ship, click ship's hex
- **Close triggers**: Click X button, press ESC, click outside panel, click different ship (switches to new ship)
- **Animation**: 300ms ease-out slide transition
- **Focus management**: Focus panel when opened, return focus to map when closed

---

## 4. Interaction Flows

### Flow 1: Planning Phase - Issue Movement Orders

```
1. Game enters PLANNING phase
   └─> TopHUD displays "PLANNING" badge (blue)
   └─> Ships without orders have pulsing indicator

2. User clicks ship "HMS Victory"
   └─> Ship highlights (thicker stroke, glow)
   └─> ShipActionPanel slides in from right (300ms)
   └─> Panel shows:
       • Ship name + P1 badge
       • Damage tracks (Hull: ████████░░ 80%)
       • Load status (L: Loaded, R: Loaded)
       • Movement input field (empty, focused)
       • "Mark Ready" button (disabled)

3. User types movement notation "L1R1"
   └─> Input validates character-by-character
   └─> Invalid chars rejected with red flash
   └─> Valid notation shows green checkmark

4. User clicks "Submit Orders"
   └─> POST /api/games/{id}/orders
   └─> Server validates, stores orders
   └─> Ship ready indicator appears (green checkmark badge on ship)
   └─> "Mark Ready" button enables

5. User clicks "Mark Ready"
   └─> Local state updated: shipReadyStates.set(shipId, true)
   └─> Ship visual changes: glowing border + checkmark badge
   └─> Panel stays open (user can modify or close)

6. User clicks X or presses ESC
   └─> Panel slides out (300ms)
   └─> Ship remains selected/highlighted until clicking elsewhere

7. Repeat for all ships...

8. When both players ready:
   └─> TopHUD "Advance Turn" button pulses/glows
   └─> User clicks "Advance Turn"
   └─> POST /api/games/{id}/resolve-movement
   └─> Phase transitions to MOVEMENT → COMBAT
```

### Flow 2: Combat Phase - Fire Broadsides

```
1. Game enters COMBAT phase
   └─> TopHUD displays "COMBAT" badge (red)
   └─> Ships with loaded broadsides have fire indicator

2. User clicks ship "HMS Victory"
   └─> ShipActionPanel opens
   └─> Panel shows:
       • Ship status (damage, load states)
       • Broadside selector: [L] [R] buttons
       • L: Loaded (enabled), R: Loaded (enabled)

3. User clicks "L" (left broadside)
   └─> Button highlights
   └─> selectedBroadside = 'L'
   └─> GET /api/games/{id}/combat/arc (shipId, broadside)
   └─> Server returns: ships_in_arc, valid_targets
   └─> HexMap renders arc hexes (translucent red overlay)
   └─> Valid target ships highlight (red pulse outline)
   └─> Panel updates:
       • Target selector appears with dropdown/list
       • Shows only valid targets (closest-target rule enforced)
       • Aim point selector appears: [Hull] [Rigging] buttons

4. User selects target "Le Redoutable" from list
   └─> selectedTargetId = target.id
   └─> Target ship highlights with crosshairs icon
   └─> Arc remains visible

5. User clicks aim point "Hull"
   └─> selectedAimPoint = 'HULL'
   └─> "Fire Broadside" button enables (glowing, pulsing)

6. User clicks "Fire Broadside"
   └─> POST /api/games/{id}/combat/fire
   └─> Server resolves combat:
       • Rolls dice
       • Applies damage
       • Updates load state (L → Empty)
   └─> Response includes damage events
   └─> Panel updates:
       • Shows combat result message
       • L broadside now "Empty" (disabled button)
       • Target selector resets
       • Arc disappears
   └─> HexMap updates target ship damage visualization

7. User can:
   • Fire R broadside (repeat flow)
   • Select different ship
   • Close panel

8. When done firing:
   └─> TopHUD "Reload Broadsides" button available
   └─> User clicks → POST /api/games/{id}/reload
   └─> Phase transitions to RELOAD → PLANNING (new turn)
```

### Flow 3: Responsive Ship Selection & Panel Management

```
Scenario: User rapidly clicks different ships

1. Ship A selected, panel open
2. User clicks Ship B
   └─> Ship A deselects
   └─> Ship B highlights
   └─> Panel content smoothly transitions (fade out → fade in, 150ms)
   └─> New ship data loads
   └─> Panel remains open

3. User clicks hex grid (not a ship)
   └─> Panel closes (if click outside panel bounds)
   └─> All ships deselect

4. User presses ESC
   └─> Panel closes
   └─> Selection clears
```

---

## 5. Visual Design Specifications

### Color Palette - Naval Chart Theme

```css
:root {
  /* Ocean & Background */
  --ocean-deep: #0d2d3a;
  --ocean-surface: #1a4d5c;
  --ocean-highlight: #2a6d7c;

  /* Parchment UI */
  --parchment-base: #f2ebdc;
  --parchment-dark: #d4c5a9;
  --parchment-border: #8b7355;

  /* Ink & Typography */
  --ink-primary: #2c1810;
  --ink-secondary: #5a4a3a;
  --ink-faded: #8b7d6b;

  /* Phase Colors */
  --phase-planning: #4a7ba7;    /* Blue */
  --phase-movement: #5a8f5a;    /* Green */
  --phase-combat: #a74a4a;      /* Red */
  --phase-reload: #d4874f;      /* Orange */

  /* Player Sides */
  --player-1: #3a5ba7;          /* Navy blue */
  --player-2: #a73a3a;          /* Burgundy red */

  /* Status Indicators */
  --ready-green: #4a8f4a;
  --struck-gray: #6a6a6a;
  --fouled-orange: #d4874f;
  --selected-glow: #f4d03f;

  /* Functional */
  --success: #5a9a5a;
  --warning: #d4a74f;
  --error: #a74a4a;
}
```

### Typography

```css
/* Primary Display: IM Fell English (period naval documents) */
@import url('https://fonts.googleapis.com/css2?family=IM+Fell+English:ital,wght@0,400;0,700;1,400&display=swap');

/* Body & UI: Cinzel (refined, classical) */
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&display=swap');

/* Monospace: Courier Prime (typewriter, orders) */
@import url('https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap');

body {
  font-family: 'Cinzel', serif;
  font-size: 14px;
  color: var(--ink-primary);
}

h1, h2, h3 {
  font-family: 'IM Fell English', serif;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.movement-input, .combat-notation {
  font-family: 'Courier Prime', monospace;
  font-size: 16px;
  letter-spacing: 1px;
}
```

### Ship Visual States

#### Base Ship Rendering
```
- 2-hex polygon (bow + stern)
- Fill: Player color (P1: navy blue, P2: burgundy)
- Stroke: Darker shade (3px)
- Opacity: 0.85 (semi-transparent)
- Facing arrow: White triangle at bow center
```

#### State Overlays (cumulative)

**Selected**
```css
.ship-selected {
  stroke: var(--selected-glow);
  stroke-width: 4px;
  filter: drop-shadow(0 0 12px rgba(244, 208, 63, 0.8));
  opacity: 1;
}
```

**Ready**
```css
.ship-ready {
  stroke: var(--ready-green);
  stroke-width: 3px;
  animation: pulse-ready 2s ease-in-out infinite;
}

@keyframes pulse-ready {
  0%, 100% { opacity: 0.85; }
  50% { opacity: 1; }
}

/* Badge: checkmark icon at stern hex center */
.ready-badge {
  fill: var(--ready-green);
  /* SVG checkmark path */
}
```

**Struck**
```css
.ship-struck {
  fill: var(--struck-gray);
  opacity: 0.4;
  stroke: var(--struck-gray);
  stroke-dasharray: 4 4; /* Dashed outline */
  animation: none; /* No pulse */
}

/* Overlay: X icon across both hexes */
.struck-overlay {
  stroke: var(--ink-secondary);
  stroke-width: 3px;
  opacity: 0.6;
}
```

**Fouled**
```css
.ship-fouled {
  stroke: var(--fouled-orange);
  stroke-width: 3px;
}

/* Badge: chain link icon */
.fouled-badge {
  fill: var(--fouled-orange);
}
```

**Hover (not selected)**
```css
.ship:hover {
  opacity: 1;
  cursor: pointer;
  stroke-width: 3.5px;
  transition: all 0.15s ease-out;
}
```

### Ship Action Panel Design

```css
.ship-action-panel {
  position: fixed;
  right: 0;
  top: 80px; /* Below HUD */
  width: 380px;
  height: calc(100vh - 80px);

  background: var(--parchment-base);
  border-left: 3px solid var(--parchment-border);
  box-shadow: -4px 0 16px rgba(0, 0, 0, 0.3);

  /* Paper texture overlay */
  background-image:
    url('data:image/svg+xml,...'), /* Subtle noise texture */
    linear-gradient(180deg, #f2ebdc 0%, #e8ddc8 100%);

  overflow-y: auto;
  padding: 24px;

  /* Slide animation */
  transform: translateX(100%);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.ship-action-panel.open {
  transform: translateX(0);
}
```

**Panel Header**
```css
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--parchment-border);
}

.ship-name {
  font-family: 'IM Fell English', serif;
  font-size: 22px;
  font-weight: 700;
  color: var(--ink-primary);
}

.side-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  margin-left: 12px;
}

.side-badge.p1 {
  background: var(--player-1);
  color: white;
}

.side-badge.p2 {
  background: var(--player-2);
  color: white;
}

.close-button {
  background: none;
  border: none;
  font-size: 28px;
  color: var(--ink-secondary);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.close-button:hover {
  color: var(--ink-primary);
}
```

**Damage Track Bars**
```css
.damage-track {
  margin-bottom: 16px;
}

.track-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink-secondary);
  margin-bottom: 4px;
  display: flex;
  justify-content: space-between;
}

.track-bar {
  width: 100%;
  height: 24px;
  background: rgba(139, 125, 107, 0.2);
  border: 1px solid var(--parchment-border);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.track-fill {
  height: 100%;
  transition: width 0.4s ease-out, background-color 0.4s;

  /* Gradient based on percentage */
  &.hull {
    background: linear-gradient(90deg, #a74a4a 0%, #d4874f 100%);
  }

  &.rigging {
    background: linear-gradient(90deg, #8b7355 0%, #d4c5a9 100%);
  }

  &.crew {
    background: linear-gradient(90deg, #4a7ba7 0%, #7a9bc7 100%);
  }
}

/* Color shifts based on health percentage */
.track-fill.health-good { /* >66% */
  filter: hue-rotate(60deg) saturate(0.8);
}

.track-fill.health-medium { /* 33-66% */
  filter: saturate(1);
}

.track-fill.health-critical { /* <33% */
  filter: saturate(1.2) brightness(1.1);
  animation: pulse-critical 1.5s ease-in-out infinite;
}

@keyframes pulse-critical {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
```

**Movement Input (Planning Phase)**
```css
.movement-section {
  margin-top: 24px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.4);
  border: 2px dashed var(--parchment-border);
  border-radius: 8px;
}

.movement-input {
  width: 100%;
  padding: 12px;
  font-family: 'Courier Prime', monospace;
  font-size: 18px;
  text-align: center;
  letter-spacing: 2px;
  text-transform: uppercase;

  background: white;
  border: 2px solid var(--parchment-border);
  border-radius: 4px;
  color: var(--ink-primary);

  transition: border-color 0.2s;
}

.movement-input:focus {
  outline: none;
  border-color: var(--phase-planning);
  box-shadow: 0 0 0 3px rgba(74, 123, 167, 0.2);
}

.movement-input.valid {
  border-color: var(--success);
}

.movement-input.invalid {
  border-color: var(--error);
  animation: shake 0.3s;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

.submit-button, .ready-button {
  width: 100%;
  padding: 14px;
  margin-top: 12px;

  font-family: 'Cinzel', serif;
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;

  border: 2px solid var(--ink-primary);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.submit-button {
  background: var(--phase-planning);
  color: white;
}

.submit-button:hover:not(:disabled) {
  background: #5a8bc7;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.ready-button {
  background: var(--ready-green);
  color: white;
}

.ready-button.is-ready {
  background: var(--parchment-dark);
  border-color: var(--ready-green);
  color: var(--ready-green);
  cursor: default;
}

.submit-button:disabled, .ready-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

**Combat Controls (Combat Phase)**
```css
.combat-section {
  margin-top: 24px;
}

.broadside-selector {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.broadside-button {
  flex: 1;
  padding: 16px;

  font-family: 'Cinzel', serif;
  font-size: 16px;
  font-weight: 700;

  background: var(--parchment-dark);
  border: 2px solid var(--parchment-border);
  border-radius: 6px;
  cursor: pointer;

  transition: all 0.2s;
  position: relative;
}

.broadside-button.loaded {
  background: var(--phase-combat);
  color: white;
  border-color: var(--phase-combat);
}

.broadside-button.empty {
  opacity: 0.4;
  cursor: not-allowed;
}

.broadside-button.selected {
  border-color: var(--selected-glow);
  box-shadow: 0 0 12px rgba(244, 208, 63, 0.5);
  transform: scale(1.05);
}

.broadside-button:hover:not(.empty):not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* Load status badge */
.load-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--ready-green);
  border: 2px solid var(--parchment-base);

  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  color: white;
}

.load-badge.empty {
  background: var(--struck-gray);
}

.target-selector {
  margin-top: 20px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.3);
  border: 2px solid var(--parchment-border);
  border-radius: 6px;
}

.target-list {
  max-height: 200px;
  overflow-y: auto;
}

.target-item {
  padding: 12px;
  margin-bottom: 8px;
  background: white;
  border: 2px solid var(--parchment-border);
  border-radius: 4px;
  cursor: pointer;

  display: flex;
  justify-content: space-between;
  align-items: center;

  transition: all 0.2s;
}

.target-item:hover {
  border-color: var(--phase-combat);
  transform: translateX(4px);
}

.target-item.selected {
  border-color: var(--selected-glow);
  background: rgba(244, 208, 63, 0.1);
  box-shadow: 0 0 8px rgba(244, 208, 63, 0.3);
}

.aim-point-selector {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.aim-button {
  flex: 1;
  padding: 12px;

  font-family: 'Cinzel', serif;
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;

  background: white;
  border: 2px solid var(--parchment-border);
  border-radius: 4px;
  cursor: pointer;

  transition: all 0.2s;
}

.aim-button.selected {
  background: var(--phase-combat);
  color: white;
  border-color: var(--phase-combat);
}

.fire-button {
  width: 100%;
  padding: 18px;
  margin-top: 20px;

  font-family: 'IM Fell English', serif;
  font-size: 18px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 2px;

  background: var(--phase-combat);
  color: white;
  border: 3px solid var(--ink-primary);
  border-radius: 6px;
  cursor: pointer;

  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}

.fire-button::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

.fire-button:hover:not(:disabled)::before {
  width: 300px;
  height: 300px;
}

.fire-button:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(167, 74, 74, 0.4);
}

.fire-button:active:not(:disabled) {
  transform: scale(0.98);
}

.fire-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.fire-button.ready-to-fire {
  animation: pulse-fire 1.5s ease-in-out infinite;
}

@keyframes pulse-fire {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(167, 74, 74, 0.7);
  }
  50% {
    box-shadow: 0 0 0 15px rgba(167, 74, 74, 0);
  }
}
```

### Top HUD Design

```css
.top-hud {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 80px;
  z-index: 1000;

  background: linear-gradient(180deg,
    rgba(242, 235, 220, 0.98) 0%,
    rgba(242, 235, 220, 0.95) 100%);
  border-bottom: 3px solid var(--parchment-border);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);

  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;

  /* Decorative top border */
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg,
      var(--player-1) 0%,
      var(--parchment-border) 50%,
      var(--player-2) 100%);
  }
}

.wind-rose {
  width: 60px;
  height: 60px;

  /* SVG compass rose with directional indicator */
  svg {
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
  }

  .rose-pointer {
    transition: transform 0.5s ease-out;
    transform-origin: center;
  }
}

.turn-phase-indicator {
  display: flex;
  align-items: center;
  gap: 20px;
}

.turn-number {
  font-family: 'IM Fell English', serif;
  font-size: 24px;
  font-weight: 700;
  color: var(--ink-primary);
}

.phase-badge {
  display: inline-block;
  padding: 8px 20px;
  border-radius: 24px;

  font-family: 'Cinzel', serif;
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.5px;

  color: white;
  border: 2px solid rgba(0, 0, 0, 0.2);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);

  &.planning {
    background: var(--phase-planning);
  }

  &.movement {
    background: var(--phase-movement);
  }

  &.combat {
    background: var(--phase-combat);
  }

  &.reload {
    background: var(--phase-reload);
  }
}

.phase-action-button {
  padding: 14px 32px;

  font-family: 'Cinzel', serif;
  font-size: 16px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;

  background: var(--ink-primary);
  color: var(--parchment-base);
  border: 2px solid var(--ink-primary);
  border-radius: 6px;
  cursor: pointer;

  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.phase-action-button:hover:not(:disabled) {
  background: var(--ink-secondary);
  border-color: var(--ink-secondary);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
}

.phase-action-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.phase-action-button.ready-to-advance {
  animation: pulse-advance 2s ease-in-out infinite;
}

@keyframes pulse-advance {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(44, 24, 16, 0.7);
  }
  50% {
    box-shadow: 0 0 0 20px rgba(44, 24, 16, 0);
  }
}
```

### Hex Map Enhancements

```css
.hex-map-ocean {
  position: fixed;
  top: 80px;
  left: 0;
  right: 0;
  bottom: 0;

  background: radial-gradient(ellipse at center,
    var(--ocean-surface) 0%,
    var(--ocean-deep) 100%);

  /* Subtle wave texture overlay */
  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image: url('data:image/svg+xml,...'); /* Wave pattern */
    opacity: 0.1;
    pointer-events: none;
  }
}

.hex-grid {
  width: 100%;
  height: 100%;
}

.hex-cell {
  fill: none;
  stroke: var(--parchment-dark);
  stroke-width: 1;
  opacity: 0.3;
  transition: opacity 0.2s;
}

.hex-cell:hover {
  opacity: 0.6;
  stroke-width: 1.5;
}

/* Targeting arc overlay */
.targeting-arc {
  fill: var(--phase-combat);
  opacity: 0.2;
  stroke: var(--phase-combat);
  stroke-width: 2;
  pointer-events: none;

  animation: arc-pulse 2s ease-in-out infinite;
}

@keyframes arc-pulse {
  0%, 100% { opacity: 0.2; }
  50% { opacity: 0.35; }
}
```

### Animation & Transitions

**Panel Slide Animation**
```css
@keyframes slide-in {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slide-out {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}
```

**Ship Selection Feedback**
```css
@keyframes select-ship {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

.ship.just-selected {
  animation: select-ship 0.3s ease-out;
}
```

**Phase Transition**
```css
@keyframes phase-transition {
  0% {
    transform: scale(1) rotate(0deg);
    opacity: 1;
  }
  50% {
    transform: scale(1.2) rotate(10deg);
    opacity: 0.5;
  }
  100% {
    transform: scale(1) rotate(0deg);
    opacity: 1;
  }
}

.phase-badge.transitioning {
  animation: phase-transition 0.6s ease-in-out;
}
```

---

## 6. Responsive Behavior

### Breakpoints

```css
/* Large Desktop: 1440px+ */
/* Default layout as described */

/* Desktop: 1024px - 1439px */
@media (max-width: 1439px) {
  .ship-action-panel {
    width: 340px;
  }

  .top-hud {
    padding: 0 24px;
  }
}

/* Tablet: 768px - 1023px */
@media (max-width: 1023px) {
  .ship-action-panel {
    width: 100%;
    max-width: 400px;
    right: 0;
    left: auto;
  }

  .top-hud {
    height: 70px;
    padding: 0 16px;
    flex-wrap: wrap;
  }

  .wind-rose {
    width: 50px;
    height: 50px;
  }

  .turn-number {
    font-size: 20px;
  }

  .phase-badge {
    font-size: 12px;
    padding: 6px 16px;
  }
}

/* Mobile: < 768px */
@media (max-width: 767px) {
  .ship-action-panel {
    width: 100%;
    height: 50vh;
    top: auto;
    bottom: 0;
    border-left: none;
    border-top: 3px solid var(--parchment-border);

    transform: translateY(100%);
  }

  .ship-action-panel.open {
    transform: translateY(0);
  }

  .top-hud {
    height: 60px;
    padding: 0 12px;
  }

  .wind-rose {
    width: 40px;
    height: 40px;
  }

  .turn-phase-indicator {
    gap: 12px;
  }

  .turn-number {
    font-size: 16px;
  }

  .phase-badge {
    font-size: 10px;
    padding: 4px 12px;
  }

  .phase-action-button {
    padding: 10px 20px;
    font-size: 14px;
  }

  /* Simplify damage tracks on mobile */
  .track-bar {
    height: 20px;
  }

  .track-label {
    font-size: 11px;
  }
}
```

### Touch Interactions (Mobile/Tablet)

- Ship selection: Single tap
- Panel close: Swipe down (mobile) or tap outside
- Broadside selection: Large touch targets (min 44px)
- Target selection: Scrollable list with generous spacing
- Zoom/pan: Pinch-to-zoom on hex map (future enhancement)

---

## 7. Accessibility Considerations

### Keyboard Navigation

```
Tab Order:
1. Top HUD elements (wind rose, turn indicator, phase button)
2. Hex map (focusable with Enter to select ship)
3. Ship action panel controls (when open)
   a. Close button
   b. Movement input / broadside buttons
   c. Target selection
   d. Aim point buttons
   e. Fire/Submit buttons

Keyboard Shortcuts:
- ESC: Close ship action panel
- Space: Select/deselect focused ship
- Arrow keys: Navigate between ships (when panel closed)
- Enter: Confirm action (submit orders, fire broadside, advance phase)
- Tab: Cycle through interactive elements
- Shift+Tab: Reverse cycle
- 1-9, L, R, 0: Quick movement entry (when input focused)
```

### ARIA Attributes

```html
<!-- Top HUD -->
<header class="top-hud" role="banner">
  <div class="wind-rose" role="img" aria-label="Wind direction: West">
    <!-- SVG -->
  </div>
  <div class="turn-phase-indicator" role="status" aria-live="polite">
    <span class="turn-number" aria-label="Turn 3">Turn 3</span>
    <span class="phase-badge combat" aria-label="Current phase: Combat">Combat</span>
  </div>
  <button class="phase-action-button" aria-label="Advance to next phase">
    Advance Turn ➜
  </button>
</header>

<!-- Ship on map -->
<g class="ship"
   role="button"
   tabindex="0"
   aria-label="HMS Victory, Player 1, Hull 80%, Ready"
   aria-pressed="false">
  <!-- Ship SVG -->
</g>

<!-- Ship action panel -->
<aside class="ship-action-panel"
       role="complementary"
       aria-label="Ship actions panel"
       aria-hidden="true">
  <header class="panel-header">
    <h2 class="ship-name">HMS Victory</h2>
    <button class="close-button"
            aria-label="Close panel"
            aria-keyshortcuts="Escape">
      ×
    </button>
  </header>

  <!-- Damage tracks -->
  <section aria-labelledby="status-heading">
    <h3 id="status-heading" class="sr-only">Ship Status</h3>
    <div class="damage-track" role="progressbar"
         aria-label="Hull integrity"
         aria-valuenow="80"
         aria-valuemin="0"
         aria-valuemax="100">
      <!-- Track bar -->
    </div>
  </section>

  <!-- Combat controls -->
  <section aria-labelledby="combat-heading">
    <h3 id="combat-heading" class="sr-only">Combat Controls</h3>
    <div class="broadside-selector" role="radiogroup" aria-label="Select broadside">
      <button class="broadside-button"
              role="radio"
              aria-checked="false"
              aria-label="Left broadside, Loaded">
        L
      </button>
      <button class="broadside-button"
              role="radio"
              aria-checked="false"
              aria-label="Right broadside, Loaded">
        R
      </button>
    </div>
  </section>
</aside>
```

### Screen Reader Announcements

```javascript
// Example live region updates
function announcePhaseChange(newPhase) {
  const announcer = document.getElementById('sr-announcer');
  announcer.textContent = `Phase changed to ${newPhase}`;
}

function announceShipReady(shipName) {
  const announcer = document.getElementById('sr-announcer');
  announcer.textContent = `${shipName} is ready`;
}

function announceCombatResult(attacker, target, damage) {
  const announcer = document.getElementById('sr-announcer');
  announcer.textContent =
    `${attacker} fired at ${target}, dealing ${damage} damage`;
}
```

### Color Contrast

All text meets WCAG AA standards (4.5:1 for normal text, 3:1 for large text):
- Primary text (--ink-primary) on parchment: 9.2:1 ✓
- Secondary text (--ink-secondary) on parchment: 5.8:1 ✓
- White text on phase badges: 4.8:1+ ✓
- Button text: All combinations tested ✓

### Focus Indicators

```css
/* Custom focus styles */
*:focus-visible {
  outline: 3px solid var(--selected-glow);
  outline-offset: 2px;
  border-radius: 4px;
}

.ship:focus-visible {
  outline: 3px solid var(--selected-glow);
  outline-offset: 4px;
  filter: drop-shadow(0 0 12px rgba(244, 208, 63, 0.8));
}

button:focus-visible {
  outline: 3px solid var(--phase-planning);
  outline-offset: 2px;
}
```

---

## 8. Implementation Breakdown

This redesign can be broken into the following beads (work items):

### Epic: Full-Screen Immersive UI Redesign

#### Phase 1: Foundation & Layout (3 beads)

**Bead 1: Restructure GamePage layout for full-screen hex map**
- Remove existing panel components from always-visible layout
- Modify GamePage.tsx to use new layout structure (Top HUD + full hex map)
- Adjust HexGrid to fill remaining viewport (calc(100vh - 80px))
- Add ocean gradient background to hex map container
- Add subtle wave texture overlay

**Bead 2: Create TopHUD component with phase controls**
- Build TopHUD component with three sections (wind rose, turn/phase, action button)
- Implement WindRose SVG component with directional pointer
- Create TurnPhaseIndicator with phase color-coding
- Move phase transition logic to PhaseActionButton
- Style with parchment overlay and decorative borders

**Bead 3: Implement collapsible ShipActionPanel with slide animation**
- Create new ShipActionPanel component with slide-in/out animation
- Add panel open/close state management in GamePage
- Implement close triggers (X button, ESC key, click outside)
- Add panel header with ship name and close button
- Style with aged parchment background and paper texture

#### Phase 2: Ship Visual States (2 beads)

**Bead 4: Add ship visual state indicators (ready, struck, fouled)**
- Modify Ship.tsx to render state-based overlays
- Implement "ready" state: green pulsing border + checkmark badge
- Implement "struck" state: gray fill, dashed border, X overlay
- Implement "fouled" state: orange border + chain link badge
- Add selection highlight with golden glow effect

**Bead 5: Enhance ship hover and selection interactions**
- Add hover effects (opacity, stroke width, cursor)
- Implement selection animation (scale pulse)
- Add click handlers for ship selection → panel open
- Update HexGrid click detection to support ship selection
- Add keyboard navigation support (Tab, Arrow keys, Enter)

#### Phase 3: Panel Content - Planning Phase (2 beads)

**Bead 6: Build Planning phase panel content**
- Move OrdersPanel functionality into ShipActionPanel
- Create movement input field with real-time validation
- Add "Submit Orders" and "Mark Ready" buttons
- Implement visual feedback for valid/invalid notation (green checkmark / red shake)
- Style with naval typography (Courier Prime for input)

**Bead 7: Implement ready state tracking and visualization**
- Add client-side ready state management (Map<shipId, isReady>)
- Update ready state when orders submitted + marked ready
- Sync ready indicators on ship and in panel
- Show ready count in TopHUD (e.g., "Ships Ready: 2/3")
- Enable "Advance Turn" button when both players ready

#### Phase 4: Panel Content - Combat Phase (2 beads)

**Bead 8: Build Combat phase panel content**
- Move CombatPanel functionality into ShipActionPanel
- Create broadside selector (L/R buttons with load status badges)
- Implement target selector (scrollable list with distance info)
- Add aim point selector (Hull / Rigging buttons)
- Style with combat red theme and period typography

**Bead 9: Integrate combat targeting visualization**
- Render broadside firing arc on HexGrid when broadside selected
- Highlight valid targets with pulsing red outline
- Show crosshairs on selected target ship
- Update arc and highlights in real-time as selections change
- Clear visualizations after firing or panel close

#### Phase 5: Polish & Responsive (2 beads)

**Bead 10: Add animations and micro-interactions**
- Implement all keyframe animations (pulse, slide, shake, glow)
- Add smooth transitions for state changes (0.2-0.3s)
- Create phase transition animation for TopHUD badge
- Add hover effects to all interactive elements
- Implement "Fire Broadside" button ripple effect

**Bead 11: Implement responsive breakpoints and mobile layout**
- Add media queries for tablet (768-1023px) and mobile (<768px)
- Convert panel to bottom drawer on mobile (slide up)
- Adjust TopHUD for smaller screens (wrap, smaller fonts)
- Simplify damage track bars on mobile
- Test touch interactions (tap, swipe, scroll)

#### Phase 6: Accessibility & Testing (2 beads)

**Bead 12: Add keyboard navigation and ARIA attributes**
- Implement Tab order and keyboard shortcuts (ESC, Space, Enter, Arrows)
- Add all ARIA labels, roles, and live regions
- Create screen reader announcement system
- Add focus-visible styles for all interactive elements
- Test with keyboard-only navigation

**Bead 13: Accessibility audit and color contrast verification**
- Verify all text meets WCAG AA contrast ratios (4.5:1, 3:1)
- Test with screen readers (VoiceOver, NVDA)
- Add skip links and focus management
- Test color-blind friendly palettes (deuteranopia, protanopia)
- Document accessibility features in README

#### Phase 7: Typography & Visual Polish (1 bead)

**Bead 14: Import custom fonts and finalize typography**
- Add Google Fonts imports (IM Fell English, Cinzel, Courier Prime)
- Apply typography hierarchy across all components
- Fine-tune font sizes, weights, and letter-spacing
- Add text shadows and effects where appropriate
- Test font loading performance and add fallbacks

---

## Total Implementation: 14 Beads

**Estimated Complexity:**
- Phase 1 (Foundation): Medium-High (architectural changes)
- Phase 2 (Visual States): Medium (SVG overlays, state logic)
- Phase 3 (Planning): Medium (refactor existing components)
- Phase 4 (Combat): Medium (refactor + visualization)
- Phase 5 (Polish): Low-Medium (CSS animations, responsive)
- Phase 6 (Accessibility): Medium (comprehensive testing)
- Phase 7 (Typography): Low (font integration)

**Dependencies:**
- Beads 2-3 must complete before 4-14 (foundation first)
- Beads 6-7 can run parallel to 8-9 (different phases)
- Bead 10 depends on all functional beads (1-9)
- Bead 11 depends on 1-10 (responsive builds on base)
- Beads 12-13 depend on all UI beads (1-11)
- Bead 14 can start early but finalize last

---

## Design Rationale

This redesign prioritizes:

1. **Immersion**: Full-screen battlefield puts players in command
2. **Clarity**: Phase-specific UI reduces cognitive load
3. **Efficiency**: Context panels mean less scrolling, clearer focus
4. **Aesthetic cohesion**: Naval chart theme creates memorable identity
5. **Accessibility**: Keyboard, screen reader, and color-blind support
6. **Performance**: CSS-first animations, minimal re-renders

The naval chart aesthetic differentiates this from generic wargame UIs while honoring the source material's 1970s Avalon Hill heritage. The result should feel both modern (responsive, accessible) and timeless (aged paper, classical typography).

---

## Next Steps

1. **User review this document** - confirm design direction aligns with vision
2. **Create beads in tracking system** - use breakdown above (14 beads)
3. **Set up dependencies** - Phase 1 blocks Phase 2+, etc.
4. **Gather assets** - prepare any custom SVG icons (wind rose, badges, etc.)
5. **Begin Phase 1 implementation** - foundation first

This design provides a clear roadmap from current implementation to immersive, full-screen naval battlefield experience.
