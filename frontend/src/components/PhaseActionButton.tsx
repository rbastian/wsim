// Phase action button with phase transition logic

import { useState } from "react";
import { api } from "../api/client";
import type { Game } from "../types/game";

interface PhaseActionButtonProps {
  game: Game;
  onGameUpdate: (game: Game) => void;
}

export function PhaseActionButton({ game, onGameUpdate }: PhaseActionButtonProps) {
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

  const canResolveMovement = () => {
    return (
      game.phase === "planning" &&
      game.p1_orders !== null &&
      game.p2_orders !== null &&
      game.p1_orders.ready &&
      game.p2_orders.ready
    );
  };

  const canResolveReload = () => {
    return game.phase === "combat";
  };

  const canAdvanceTurn = () => {
    return game.phase === "reload";
  };

  const getButtonText = () => {
    if (loading) {
      switch (game.phase) {
        case "planning":
          return "Resolving...";
        case "combat":
          return "Reloading...";
        case "reload":
          return "Advancing...";
        default:
          return "Processing...";
      }
    }

    switch (game.phase) {
      case "planning":
        return "Resolve Movement ➜";
      case "combat":
        return "Reload Broadsides ➜";
      case "reload":
        return `Advance to Turn ${game.turn_number + 1} ➜`;
      case "movement":
        return "Movement Complete";
      default:
        return "Continue";
    }
  };

  const handleClick = () => {
    switch (game.phase) {
      case "planning":
        handleResolveMovement();
        break;
      case "combat":
        handleResolveReload();
        break;
      case "reload":
        handleAdvanceTurn();
        break;
      default:
        break;
    }
  };

  const isEnabled = () => {
    switch (game.phase) {
      case "planning":
        return canResolveMovement() && !loading;
      case "combat":
        return canResolveReload() && !loading;
      case "reload":
        return canAdvanceTurn() && !loading;
      default:
        return false;
    }
  };

  const bothPlayersReady = () => {
    return (
      game.phase === "planning" &&
      game.p1_orders?.ready &&
      game.p2_orders?.ready
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
      <button
        className={`phase-action-button ${bothPlayersReady() ? 'ready-to-advance' : ''}`}
        onClick={handleClick}
        disabled={!isEnabled()}
        aria-label={getButtonText()}
        aria-disabled={!isEnabled()}
        style={{
          padding: '14px 32px',
          fontFamily: "'Cinzel', serif",
          fontSize: '16px',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '1px',
          background: isEnabled() ? '#2c1810' : '#d4c5a9',
          color: isEnabled() ? '#f2ebdc' : '#8b7d6b',
          border: `2px solid ${isEnabled() ? '#2c1810' : '#8b7355'}`,
          borderRadius: '6px',
          cursor: isEnabled() ? 'pointer' : 'not-allowed',
          transition: 'all 0.3s',
          position: 'relative',
          overflow: 'hidden',
          opacity: isEnabled() ? 1 : 0.6,
        }}
        onMouseEnter={(e) => {
          if (isEnabled()) {
            e.currentTarget.style.background = '#5a4a3a';
            e.currentTarget.style.borderColor = '#5a4a3a';
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 6px 16px rgba(0, 0, 0, 0.3)';
          }
        }}
        onMouseLeave={(e) => {
          if (isEnabled()) {
            e.currentTarget.style.background = '#2c1810';
            e.currentTarget.style.borderColor = '#2c1810';
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = 'none';
          }
        }}
      >
        {getButtonText()}
      </button>

      {/* Error display */}
      {error && (
        <div
          role="alert"
          aria-live="assertive"
          style={{
            padding: '8px 12px',
            backgroundColor: 'rgba(167, 74, 74, 0.1)',
            border: '1px solid #a74a4a',
            borderRadius: '4px',
            color: '#a74a4a',
            fontSize: '12px',
            maxWidth: '300px',
            textAlign: 'right',
          }}
        >
          {error}
        </div>
      )}

      {/* Add pulse/glow animation for ready-to-advance state */}
      <style>{`
        @keyframes pulse-glow {
          0%, 100% {
            box-shadow: 0 0 20px rgba(74, 123, 167, 0.6), 0 0 40px rgba(74, 123, 167, 0.4);
          }
          50% {
            box-shadow: 0 0 30px rgba(74, 123, 167, 0.8), 0 0 60px rgba(74, 123, 167, 0.6);
          }
        }

        .ready-to-advance {
          animation: pulse-glow 2s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
