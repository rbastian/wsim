// Phase control panel for managing game phase transitions

import { useState } from "react";
import { api } from "../api/client";
import type { Game } from "../types/game";

interface PhaseControlPanelProps {
  game: Game;
  onGameUpdate: (game: Game) => void;
}

export function PhaseControlPanel({ game, onGameUpdate }: PhaseControlPanelProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleResolveMovement = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.resolveMovement(game.id, game.turn_number);
      onGameUpdate(response.state);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resolve movement");
      console.error("Failed to resolve movement:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleResolveReload = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.resolveReload(game.id, game.turn_number);
      onGameUpdate(response.state);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resolve reload");
      console.error("Failed to resolve reload:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAdvanceTurn = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.advanceTurn(game.id, game.turn_number);
      onGameUpdate(response.state);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to advance turn");
      console.error("Failed to advance turn:", err);
    } finally {
      setLoading(false);
    }
  };

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case "planning":
        return "#4a90e2";
      case "movement":
        return "#50c878";
      case "combat":
        return "#e74c3c";
      case "reload":
        return "#f39c12";
      default:
        return "#888";
    }
  };

  const canResolveMovement = () => {
    return (
      game.phase === "planning" &&
      game.p1_orders !== null &&
      game.p2_orders !== null
    );
  };

  const canResolveReload = () => {
    return game.phase === "combat";
  };

  const canAdvanceTurn = () => {
    return game.phase === "reload";
  };

  const getPhaseInstructions = () => {
    switch (game.phase) {
      case "planning":
        if (!game.p1_orders || !game.p2_orders) {
          const waitingFor = [];
          if (!game.p1_orders) waitingFor.push("P1");
          if (!game.p2_orders) waitingFor.push("P2");
          return `Waiting for ${waitingFor.join(" and ")} to submit orders and mark ready.`;
        }
        return "Both players ready! Click 'Resolve Movement' to execute orders.";
      case "movement":
        return "Movement complete. Ships have moved and collisions resolved. Proceed to combat.";
      case "combat":
        return "Combat phase. Fire broadsides using the combat panel. Click 'Reload' when done.";
      case "reload":
        return "Reload complete. Click 'Advance Turn' to start the next turn.";
      default:
        return "";
    }
  };

  return (
    <div
      style={{
        backgroundColor: "#1e1e1e",
        border: "2px solid #333",
        borderRadius: "8px",
        padding: "16px",
        color: "#e0e0e0",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
        flexShrink: 0,
      }}
    >
      {/* Phase indicator */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          marginBottom: "8px",
        }}
      >
        <div
          style={{
            width: "12px",
            height: "12px",
            borderRadius: "50%",
            backgroundColor: getPhaseColor(game.phase),
          }}
        />
        <h3
          style={{
            margin: 0,
            fontSize: "16px",
            fontWeight: "bold",
            color: "#fff",
          }}
        >
          {game.phase.toUpperCase()} PHASE
        </h3>
      </div>

      {/* Instructions */}
      <p
        style={{
          margin: 0,
          fontSize: "13px",
          color: "#aaa",
          lineHeight: "1.4",
        }}
      >
        {getPhaseInstructions()}
      </p>

      {/* Error display */}
      {error && (
        <div
          style={{
            padding: "8px",
            backgroundColor: "#3d1f1f",
            border: "1px solid #e74c3c",
            borderRadius: "4px",
            color: "#e74c3c",
            fontSize: "12px",
          }}
        >
          {error}
        </div>
      )}

      {/* Action buttons */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "8px",
          marginTop: "8px",
        }}
      >
        {game.phase === "planning" && (
          <button
            onClick={handleResolveMovement}
            disabled={!canResolveMovement() || loading}
            style={{
              padding: "12px",
              backgroundColor: canResolveMovement() ? "#50c878" : "#444",
              color: canResolveMovement() ? "#fff" : "#888",
              border: "none",
              borderRadius: "6px",
              fontSize: "14px",
              fontWeight: "bold",
              cursor: canResolveMovement() && !loading ? "pointer" : "not-allowed",
              transition: "all 0.2s",
            }}
          >
            {loading ? "Resolving..." : "⚡ Resolve Movement"}
          </button>
        )}

        {game.phase === "movement" && (
          <div
            style={{
              padding: "12px",
              backgroundColor: "#2a4a2a",
              border: "1px solid #50c878",
              borderRadius: "6px",
              fontSize: "13px",
              color: "#aaa",
              textAlign: "center",
            }}
          >
            ✓ Movement complete. Continue to combat phase.
          </div>
        )}

        {game.phase === "combat" && (
          <button
            onClick={handleResolveReload}
            disabled={!canResolveReload() || loading}
            style={{
              padding: "12px",
              backgroundColor: canResolveReload() ? "#f39c12" : "#444",
              color: canResolveReload() ? "#fff" : "#888",
              border: "none",
              borderRadius: "6px",
              fontSize: "14px",
              fontWeight: "bold",
              cursor: canResolveReload() && !loading ? "pointer" : "not-allowed",
              transition: "all 0.2s",
            }}
          >
            {loading ? "Reloading..." : "🔄 Reload Broadsides"}
          </button>
        )}

        {game.phase === "reload" && (
          <button
            onClick={handleAdvanceTurn}
            disabled={!canAdvanceTurn() || loading}
            style={{
              padding: "12px",
              backgroundColor: canAdvanceTurn() ? "#4a90e2" : "#444",
              color: canAdvanceTurn() ? "#fff" : "#888",
              border: "none",
              borderRadius: "6px",
              fontSize: "14px",
              fontWeight: "bold",
              cursor: canAdvanceTurn() && !loading ? "pointer" : "not-allowed",
              transition: "all 0.2s",
            }}
          >
            {loading ? "Advancing..." : "➡️ Advance to Turn " + (game.turn_number + 1)}
          </button>
        )}
      </div>

      {/* Turn info */}
      <div
        style={{
          marginTop: "8px",
          paddingTop: "12px",
          borderTop: "1px solid #333",
          fontSize: "12px",
          color: "#666",
          textAlign: "center",
        }}
      >
        Turn {game.turn_number}
        {game.turn_limit && ` of ${game.turn_limit}`}
      </div>
    </div>
  );
}
