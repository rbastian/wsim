// TypeScript types for WSIM game models
// These mirror the Pydantic models in backend/wsim_core/models

export type Side = "P1" | "P2";

export type Facing = "N" | "NE" | "E" | "SE" | "S" | "SW" | "W" | "NW";

export type WindDirection = "N" | "NE" | "E" | "SE" | "S" | "SW" | "W" | "NW";

export type LoadState = "E" | "R"; // E = Empty, R = Roundshot

export type GamePhase = "planning" | "movement" | "combat" | "reload";

export type Broadside = "L" | "R"; // L = Left, R = Right

export type AimPoint = "hull" | "rigging";

export interface HexCoord {
  col: number;
  row: number;
}

export interface Ship {
  id: string;
  name: string;
  side: Side;
  bow_hex: HexCoord;
  stern_hex: HexCoord;
  facing: Facing;
  battle_sail_speed: number;
  guns_L: number;
  guns_R: number;
  carronades_L: number;
  carronades_R: number;
  hull: number;
  rigging: number;
  crew: number;
  marines: number;
  load_L: LoadState;
  load_R: LoadState;
  fouled: boolean;
  struck: boolean;
  turns_without_bow_advance: number;
}

export interface ShipOrders {
  ship_id: string;
  movement: string;
}

export interface TurnOrders {
  turn_number: number;
  side: Side;
  orders: ShipOrders[];
  ready: boolean;
}

export interface DiceRoll {
  num_dice: number;
  die_type: number;
  rolls: number[];
  total: number;
}

export interface EventLogEntry {
  turn_number: number;
  phase: GamePhase;
  event_type: string;
  summary: string;
  dice_roll?: DiceRoll;
  modifiers?: Record<string, number>;
  state_diff?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface Game {
  id: string;
  scenario_id: string;
  turn_number: number;
  phase: GamePhase;
  map_width: number;
  map_height: number;
  wind_direction: WindDirection;
  ships: Record<string, Ship>;
  p1_orders: TurnOrders | null;
  p2_orders: TurnOrders | null;
  event_log: EventLogEntry[];
  turn_limit: number | null;
  victory_condition: string;
}

// Scenario types
export interface MapConfig {
  width: number;
  height: number;
}

export interface WindConfig {
  direction: WindDirection;
}

export interface VictoryConfig {
  type: string;
  metric?: string;
}

export interface ShipStartPosition {
  bow: [number, number];
  facing: Facing;
}

export interface ShipGuns {
  L: number;
  R: number;
}

export interface ShipCarronades {
  L: number;
  R: number;
}

export interface ShipInitialLoad {
  L: LoadState;
  R: LoadState;
}

export interface ScenarioShip {
  id: string;
  side: Side;
  name: string;
  battle_sail_speed: number;
  start: ShipStartPosition;
  guns: ShipGuns;
  carronades: ShipCarronades;
  hull: number;
  rigging: number;
  crew: number;
  marines: number;
  initial_load: ShipInitialLoad;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  map: MapConfig;
  wind: WindConfig;
  turn_limit: number | null;
  victory: VictoryConfig;
  ships: ScenarioShip[];
}

export interface ScenarioInfo {
  id: string;
  name: string;
  description: string;
}

// API request/response types
export interface CreateGameRequest {
  scenario_id: string;
}

export interface CreateGameResponse {
  game_id: string;
  state: Game;
}

export interface SubmitOrdersRequest {
  side: Side;
  orders: ShipOrders[];
}

export interface SubmitOrdersResponse {
  state: Game;
  orders_submitted: boolean;
}

export interface MarkReadyRequest {
  side: Side;
}

export interface MarkReadyResponse {
  state: Game;
  ready: boolean;
  both_ready: boolean;
}

export interface AdvanceTurnResponse {
  state: Game;
}

export interface ResolvePhaseResponse {
  state: Game;
  events: EventLogEntry[];
}

export interface FireBroadsideRequest {
  ship_id: string;
  broadside: Broadside;
  target_ship_id: string;
  aim: AimPoint;
}

export interface FireBroadsideResponse {
  state: Game;
  events: EventLogEntry[];
}
