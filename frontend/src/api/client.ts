// API client for WSIM FastAPI backend

import type {
  CreateGameRequest,
  CreateGameResponse,
  FireBroadsideRequest,
  FireBroadsideResponse,
  Game,
  MarkReadyRequest,
  MarkReadyResponse,
  ResolvePhaseResponse,
  Scenario,
  SubmitOrdersRequest,
  SubmitOrdersResponse,
} from "../types/game";

// API base URL - default to localhost:8000 for dev
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

class ApiError extends Error {
  status?: number;
  data?: unknown;

  constructor(message: string, status?: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

async function fetchJson<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        `API error: ${response.statusText}`,
        response.status,
        errorData
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(`Network error: ${(error as Error).message}`);
  }
}

// API endpoints
export const api = {
  // Health check
  health: () => fetchJson<{ status: string }>("/health"),

  // Scenarios
  listScenarios: () => fetchJson<Scenario[]>("/scenarios"),
  getScenario: (scenarioId: string) =>
    fetchJson<Scenario>(`/scenarios/${scenarioId}`),

  // Game management
  createGame: (request: CreateGameRequest) =>
    fetchJson<CreateGameResponse>("/games", {
      method: "POST",
      body: JSON.stringify(request),
    }),

  getGame: (gameId: string) => fetchJson<{ state: Game }>(`/games/${gameId}`),

  // Orders and ready gate
  submitOrders: (gameId: string, turn: number, request: SubmitOrdersRequest) =>
    fetchJson<SubmitOrdersResponse>(`/games/${gameId}/turns/${turn}/orders`, {
      method: "POST",
      body: JSON.stringify(request),
    }),

  markReady: (gameId: string, turn: number, request: MarkReadyRequest) =>
    fetchJson<MarkReadyResponse>(`/games/${gameId}/turns/${turn}/ready`, {
      method: "POST",
      body: JSON.stringify(request),
    }),

  // Phase resolution
  resolveMovement: (gameId: string, turn: number) =>
    fetchJson<ResolvePhaseResponse>(
      `/games/${gameId}/turns/${turn}/resolve/movement`,
      { method: "POST" }
    ),

  resolveCombat: (gameId: string, turn: number) =>
    fetchJson<ResolvePhaseResponse>(
      `/games/${gameId}/turns/${turn}/resolve/combat`,
      { method: "POST" }
    ),

  resolveReload: (gameId: string, turn: number) =>
    fetchJson<ResolvePhaseResponse>(
      `/games/${gameId}/turns/${turn}/resolve/reload`,
      { method: "POST" }
    ),

  advanceTurn: (gameId: string, turn: number) =>
    fetchJson<{ state: Game }>(`/games/${gameId}/turns/${turn}/advance`, {
      method: "POST",
    }),

  // Combat firing
  fireBroadside: (gameId: string, turn: number, request: FireBroadsideRequest) =>
    fetchJson<FireBroadsideResponse>(
      `/games/${gameId}/turns/${turn}/combat/fire`,
      {
        method: "POST",
        body: JSON.stringify(request),
      }
    ),
};

export { ApiError };
