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
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      style={{
        filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2))',
      }}
    >
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

      {/* Wind direction pointer (arrow) */}
      <g
        transform={`rotate(${angle} 50 50)`}
        style={{
          transition: 'transform 0.5s ease-out',
          transformOrigin: 'center',
        }}
      >
        {/* Arrow shaft */}
        <line
          x1="50"
          y1="50"
          x2="50"
          y2="12"
          stroke="#2c1810"
          strokeWidth="3"
          strokeLinecap="round"
        />

        {/* Arrowhead */}
        <path
          d="M 50 8 L 45 18 L 50 15 L 55 18 Z"
          fill="#2c1810"
          stroke="none"
        />

        {/* Decorative tail */}
        <path
          d="M 45 52 L 50 50 L 55 52"
          fill="none"
          stroke="#2c1810"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </g>

      {/* Center dot */}
      <circle
        cx="50"
        cy="50"
        r="4"
        fill="#2c1810"
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
  );
}
