// Top HUD component with wind rose, turn/phase indicator, and phase action button

import { WindRose } from "./WindRose";
import { TurnPhaseIndicator } from "./TurnPhaseIndicator";
import { PhaseActionButton } from "./PhaseActionButton";
import type { Game } from "../types/game";

interface TopHUDProps {
  game: Game;
  onGameUpdate: (game: Game) => void;
  shipReadyState: Map<string, boolean>;
}

export function TopHUD({ game, onGameUpdate, shipReadyState }: TopHUDProps) {
  // Calculate ready count for planning phase
  const getReadyStats = () => {
    if (game.phase !== 'planning') return null;

    const allShips = Object.values(game.ships).filter(ship => !ship.struck);
    const readyCount = allShips.filter(ship => shipReadyState.get(ship.id) || false).length;
    const totalCount = allShips.length;

    return { ready: readyCount, total: totalCount };
  };

  const readyStats = getReadyStats();
  return (
    <div
      className="top-hud"
      style={{
        height: '80px',
        flexShrink: 0,
        background: 'linear-gradient(180deg, rgba(242, 235, 220, 0.98) 0%, rgba(242, 235, 220, 0.95) 100%)',
        borderBottom: '3px solid #8b7355',
        boxShadow: '0 2px 12px rgba(0, 0, 0, 0.15)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 32px',
        position: 'relative',
        zIndex: 1000,
      }}
    >
      {/* Decorative top border */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '4px',
          background: 'linear-gradient(90deg, #3a5ba7 0%, #8b7355 50%, #a73a3a 100%)',
        }}
      />

      {/* Left: Wind Rose */}
      <div className="wind-rose-container" style={{ flex: '0 0 auto' }}>
        <WindRose direction={game.wind_direction} size={60} />
      </div>

      {/* Center: Turn and Phase Indicator */}
      <div className="turn-phase-indicator" style={{ flex: '0 0 auto' }}>
        <TurnPhaseIndicator
          turn={game.turn_number}
          phase={game.phase}
          turnLimit={game.turn_limit}
        />
      </div>

      {/* Ready Count Indicator (Planning Phase Only) */}
      {readyStats && (
        <div
          className="ready-count-indicator"
          style={{
            flex: '0 0 auto',
            display: 'flex',
            alignItems: 'center',
            padding: '8px 16px',
            background: 'rgba(74, 123, 167, 0.1)',
            border: '2px solid #4a7ba7',
            borderRadius: '6px',
            fontFamily: "'Cinzel', serif",
            fontSize: '14px',
            fontWeight: 600,
            color: '#2c1810',
            letterSpacing: '0.5px',
          }}
        >
          <span style={{ marginRight: '8px' }}>⚓</span>
          <span>Ships Ready: {readyStats.ready}/{readyStats.total}</span>
        </div>
      )}

      {/* Right: Phase Action Button */}
      <div style={{ flex: '0 0 auto' }}>
        <PhaseActionButton game={game} onGameUpdate={onGameUpdate} />
      </div>
    </div>
  );
}
