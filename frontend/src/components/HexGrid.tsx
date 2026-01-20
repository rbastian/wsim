import { useMemo } from 'react';
import type { HexCoordinate, HexLayout } from '../types/hex';
import type { Ship as ShipData } from '../types/game';
import {
  hexToPixel,
  getHexCorners,
  cornersToPoints,
} from '../types/hex';
import { Ship } from './Ship';

interface HexGridProps {
  width: number;
  height: number;
  hexSize?: number;
  ships?: ShipData[];
  selectedShipId?: string | null;
  onHexClick?: (hex: HexCoordinate) => void;
  onShipClick?: (shipId: string) => void;
  arcHexes?: [number, number][];
  shipsInArc?: string[];
  validTargets?: string[];
}

interface Hex {
  coord: HexCoordinate;
  points: string;
  center: { x: number; y: number };
}

export function HexGrid({
  width,
  height,
  hexSize = 30,
  ships = [],
  selectedShipId = null,
  onHexClick,
  onShipClick,
  arcHexes = [],
  shipsInArc = [],
  validTargets = [],
}: HexGridProps) {
  const layout = useMemo<HexLayout>(() => ({
    hexSize,
    origin: { x: hexSize * 1.5, y: hexSize * Math.sqrt(3) },
    orientation: 'flat' as const,
  }), [hexSize]);

  const hexes = useMemo<Hex[]>(() => {
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
  }, [width, height, hexSize, layout]);

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

  const handleShipClick = (shipId: string) => {
    if (onShipClick) {
      onShipClick(shipId);
    }
  };

  // Create a set of arc hexes for quick lookup
  const arcHexSet = useMemo(() => {
    const set = new Set<string>();
    arcHexes.forEach(([col, row]) => {
      set.add(`${col},${row}`);
    });
    return set;
  }, [arcHexes]);

  // Check if a hex is in the arc
  const isHexInArc = (coord: HexCoordinate): boolean => {
    return arcHexSet.has(`${coord.col},${coord.row}`);
  };

  // Create a set of valid targets for quick lookup
  const validTargetSet = useMemo(() => new Set(validTargets), [validTargets]);

  // Create a set of ships in arc for quick lookup
  const shipsInArcSet = useMemo(() => new Set(shipsInArc), [shipsInArc]);

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
      {/* Hex grid layer */}
      {hexes.map((hex) => {
        const inArc = isHexInArc(hex.coord);
        const arcFill = inArc ? '#ff990055' : 'transparent';
        const arcStroke = inArc ? '#ff9900' : '#1e3a5f';
        const arcStrokeWidth = inArc ? '2' : '1.5';

        return (
          <g key={`${hex.coord.col}-${hex.coord.row}`}>
            <polygon
              points={hex.points}
              fill={arcFill}
              stroke={arcStroke}
              strokeWidth={arcStrokeWidth}
              style={{
                cursor: onHexClick ? 'pointer' : 'default',
                transition: 'fill 0.2s, stroke 0.2s',
              }}
              onClick={() => handleHexClick(hex.coord)}
              onMouseEnter={(e) => {
                if (onHexClick && !inArc) {
                  e.currentTarget.setAttribute('fill', '#1e3a5f33');
                }
              }}
              onMouseLeave={(e) => {
                if (!inArc) {
                  e.currentTarget.setAttribute('fill', 'transparent');
                }
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
        );
      })}

      {/* Ships layer */}
      {ships.map((ship) => {
        const isValidTarget = validTargetSet.has(ship.id);
        const isInArc = shipsInArcSet.has(ship.id);

        return (
          <Ship
            key={ship.id}
            ship={ship}
            layout={layout}
            isSelected={ship.id === selectedShipId}
            onClick={handleShipClick}
            isValidTarget={isValidTarget}
            isInArc={isInArc}
          />
        );
      })}
    </svg>
  );
}
