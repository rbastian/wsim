// WindRose SVG component with directional pointer

interface WindRoseProps {
  direction: string; // "N", "NE", "E", "SE", "S", "SW", "W", "NW"
  size?: number;
}

const DIRECTION_ANGLES: Record<string, number> = {
  N: 0,
  NE: 45,
  E: 90,
  SE: 135,
  S: 180,
  SW: 225,
  W: 270,
  NW: 315,
};

export function WindRose({ direction, size = 60 }: WindRoseProps) {
  const angle = DIRECTION_ANGLES[direction] || 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        role="img"
        aria-label={`Wind from ${direction}`}
        style={{
          filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2))',
        }}
      >
      <title>Wind from {direction}</title>
      {/* Outer circle */}
      <circle
        cx="50"
        cy="50"
        r="45"
        fill="none"
        stroke="#8b7355"
        strokeWidth="2"
      />

      {/* Inner decorative circle */}
      <circle
        cx="50"
        cy="50"
        r="35"
        fill="none"
        stroke="#d4c5a9"
        strokeWidth="1"
        opacity="0.5"
      />

      {/* Cardinal directions background */}
      {[0, 90, 180, 270].map((deg, i) => (
        <line
          key={`cardinal-${i}`}
          x1="50"
          y1="50"
          x2="50"
          y2="10"
          stroke="#8b7355"
          strokeWidth="2"
          opacity="0.3"
          transform={`rotate(${deg} 50 50)`}
        />
      ))}

      {/* Intercardinal directions background */}
      {[45, 135, 225, 315].map((deg, i) => (
        <line
          key={`intercardinal-${i}`}
          x1="50"
          y1="50"
          x2="50"
          y2="15"
          stroke="#8b7355"
          strokeWidth="1"
          opacity="0.3"
          transform={`rotate(${deg} 50 50)`}
        />
      ))}

      {/* Wind direction pointer (arrow) - shows where wind comes FROM */}
      <g
        transform={`rotate(${angle} 50 50)`}
        style={{
          transition: 'transform 0.5s ease-out',
          transformOrigin: 'center',
        }}
      >
        {/* Arrow shaft - thicker and blue-tinted for clarity */}
        <line
          x1="50"
          y1="50"
          x2="50"
          y2="12"
          stroke="#1a4d5c"
          strokeWidth="4"
          strokeLinecap="round"
        />

        {/* Arrowhead - larger and more prominent */}
        <path
          d="M 50 6 L 43 20 L 50 16 L 57 20 Z"
          fill="#1a4d5c"
          stroke="none"
        />

        {/* Decorative tail feathers */}
        <path
          d="M 45 54 L 50 50 L 55 54"
          fill="none"
          stroke="#1a4d5c"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Secondary tail feather */}
        <path
          d="M 46 58 L 50 55 L 54 58"
          fill="none"
          stroke="#1a4d5c"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity="0.6"
        />
      </g>

      {/* Center dot */}
      <circle
        cx="50"
        cy="50"
        r="4"
        fill="#1a4d5c"
      />

      {/* Direction label */}
      <text
        x="50"
        y="72"
        textAnchor="middle"
        dominantBaseline="middle"
        fill="#2c1810"
        fontSize="12"
        fontWeight="700"
        fontFamily="'Cinzel', serif"
      >
        {direction}
      </text>
    </svg>
    <div style={{
      fontSize: '11px',
      fontWeight: 600,
      color: '#2c1810',
      fontFamily: "'Cinzel', serif",
      letterSpacing: '0.5px',
      textAlign: 'center',
    }}>
      Wind From
    </div>
  </div>
  );
}
