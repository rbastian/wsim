// Turn and phase indicator with color-coded phase badges

interface TurnPhaseIndicatorProps {
  turn: number;
  phase: string;
  turnLimit?: number | null;
}

const PHASE_COLORS: Record<string, string> = {
  planning: '#4a7ba7',
  movement: '#5a8f5a',
  combat: '#a74a4a',
  reload: '#d4874f',
};

export function TurnPhaseIndicator({ turn, phase, turnLimit }: TurnPhaseIndicatorProps) {
  const phaseColor = PHASE_COLORS[phase] || '#888';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
      {/* Turn number */}
      <span
        style={{
          fontFamily: "'IM Fell English', serif",
          fontSize: '24px',
          fontWeight: 700,
          color: '#2c1810',
        }}
      >
        Turn {turn}
        {turnLimit && <span style={{ fontSize: '16px', opacity: 0.6 }}> of {turnLimit}</span>}
      </span>

      {/* Phase badge */}
      <span
        style={{
          padding: '8px 20px',
          borderRadius: '24px',
          fontSize: '14px',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '1.5px',
          color: 'white',
          border: '2px solid rgba(0, 0, 0, 0.2)',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
          background: phaseColor,
          fontFamily: "'Cinzel', serif",
        }}
      >
        {phase}
      </span>
    </div>
  );
}
