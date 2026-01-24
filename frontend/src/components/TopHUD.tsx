// Top HUD component with wind rose, turn/phase indicator, and phase action button

import { WindRose } from "./WindRose";
import { TurnPhaseIndicator } from "./TurnPhaseIndicator";
import { PhaseActionButton } from "./PhaseActionButton";
import type { Game } from "../types/game";

interface TopHUDProps {
  game: Game;
  onGameUpdate: (game: Game) => void;
}

export function TopHUD({ game, onGameUpdate }: TopHUDProps) {
  return (
    <div
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
      <div style={{ flex: '0 0 auto' }}>
        <WindRose direction={game.wind_direction} size={60} />
      </div>

      {/* Center: Turn and Phase Indicator */}
      <div style={{ flex: '0 0 auto' }}>
        <TurnPhaseIndicator
          turn={game.turn_number}
          phase={game.phase}
          turnLimit={game.turn_limit}
        />
      </div>

      {/* Right: Phase Action Button */}
      <div style={{ flex: '0 0 auto' }}>
        <PhaseActionButton game={game} onGameUpdate={onGameUpdate} />
      </div>
    </div>
  );
}
