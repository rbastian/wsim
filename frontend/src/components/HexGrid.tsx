import { useMemo } from 'react';
import type { HexCoordinate, HexLayout } from '../types/hex';
import {
  hexToPixel,
  getHexCorners,
  cornersToPoints,
} from '../types/hex';

interface HexGridProps {
  width: number;
  height: number;
  hexSize?: number;
  onHexClick?: (hex: HexCoordinate) => void;
}

interface Hex {
  coord: HexCoordinate;
  points: string;
  center: { x: number; y: number };
}

export function HexGrid({ width, height, hexSize = 30, onHexClick }: HexGridProps) {
  const hexes = useMemo<Hex[]>(() => {
    const layout: HexLayout = {
      hexSize,
      origin: { x: hexSize * 1.5, y: hexSize * Math.sqrt(3) },
      orientation: 'flat',
    };

    const result: Hex[] = [];

    for (let row = 0; row < height; row++) {
      for (let col = 0; col < width; col++) {
        const coord: HexCoordinate = { col, row };
        const center = hexToPixel(coord, layout);
        const corners = getHexCorners(center, hexSize);
        const points = cornersToPoints(corners);

        result.push({
          coord,
          points,
          center,
        });
      }
    }

    return result;
  }, [width, height, hexSize]);

  // Calculate SVG dimensions based on hex layout
  const svgWidth = useMemo(
    () => hexSize * (3/2) * width + hexSize * 2,
    [width, hexSize]
  );

  const svgHeight = useMemo(
    () => hexSize * Math.sqrt(3) * (height + 0.5) + hexSize * Math.sqrt(3),
    [height, hexSize]
  );

  const handleHexClick = (hex: HexCoordinate) => {
    if (onHexClick) {
      onHexClick(hex);
    }
  };

  return (
    <svg
      width="100%"
      height="100%"
      viewBox={`0 0 ${svgWidth} ${svgHeight}`}
      style={{
        border: '1px solid #333',
        backgroundColor: '#0a1929',
        maxWidth: '100%',
        height: 'auto',
      }}
    >
      {hexes.map((hex) => (
        <g key={`${hex.coord.col}-${hex.coord.row}`}>
          <polygon
            points={hex.points}
            fill="transparent"
            stroke="#1e3a5f"
            strokeWidth="1.5"
            style={{
              cursor: onHexClick ? 'pointer' : 'default',
              transition: 'fill 0.2s',
            }}
            onClick={() => handleHexClick(hex.coord)}
            onMouseEnter={(e) => {
              if (onHexClick) {
                e.currentTarget.setAttribute('fill', '#1e3a5f33');
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.setAttribute('fill', 'transparent');
            }}
          />
          <text
            x={hex.center.x}
            y={hex.center.y}
            textAnchor="middle"
            dominantBaseline="middle"
            fill="#4a5f7f"
            fontSize={hexSize * 0.3}
            style={{ pointerEvents: 'none', userSelect: 'none' }}
          >
            {hex.coord.col},{hex.coord.row}
          </text>
        </g>
      ))}
    </svg>
  );
}
