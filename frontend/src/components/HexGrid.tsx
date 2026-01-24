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
  selectedTargetId?: string | null;
  pathPreviewHexes?: [number, number][];
  readyShips?: Set<string>;
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
  selectedTargetId = null,
  pathPreviewHexes = [],
  readyShips = new Set(),
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

  const handleShipKeyDown = (e: React.KeyboardEvent, shipId: string) => {
    // Handle arrow key navigation between ships
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
      e.preventDefault();

      const currentIndex = ships.findIndex(s => s.id === shipId);
      if (currentIndex === -1) return;

      let nextIndex = currentIndex;

      if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
        nextIndex = (currentIndex + 1) % ships.length;
      } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        nextIndex = (currentIndex - 1 + ships.length) % ships.length;
      }

      const nextShip = ships[nextIndex];
      if (nextShip && onShipClick) {
        onShipClick(nextShip.id);
      }
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

  // Create a set of path preview hexes for quick lookup
  const pathPreviewHexSet = useMemo(() => {
    const set = new Set<string>();
    pathPreviewHexes.forEach(([col, row]) => {
      set.add(`${col},${row}`);
    });
    return set;
  }, [pathPreviewHexes]);

  // Check if a hex is in the path preview
  const isHexInPathPreview = (coord: HexCoordinate): boolean => {
    return pathPreviewHexSet.has(`${coord.col},${coord.row}`);
  };

  return (
    <svg
      width="100%"
      height="100%"
      viewBox={`0 0 ${svgWidth} ${svgHeight}`}
      style={{
        backgroundColor: 'transparent',
        maxWidth: '100%',
        height: 'auto',
      }}
    >
      {/* Hex grid layer */}
      {hexes.map((hex) => {
        const inArc = isHexInArc(hex.coord);
        const inPathPreview = isHexInPathPreview(hex.coord);

        // Path preview takes precedence over arc visualization
        let hexFill = 'transparent';
        let hexStroke = '#d4c5a9';  // Cream/tan nautical color
        let hexStrokeWidth = '1';
        let hexOpacity = 0.3;

        if (inPathPreview) {
          hexFill = 'rgba(74, 123, 167, 0.3)';  // Planning blue semi-transparent
          hexStroke = '#4a7ba7';  // Planning blue border
          hexStrokeWidth = '2';
          hexOpacity = 1;
        } else if (inArc) {
          hexFill = 'rgba(167, 74, 74, 0.2)';  // Combat red semi-transparent for arc
          hexStroke = '#a74a4a';  // Combat red border
          hexStrokeWidth = '2';
          hexOpacity = 1;
        }

        return (
          <g key={`${hex.coord.col}-${hex.coord.row}`}>
            <polygon
              points={hex.points}
              fill={hexFill}
              stroke={hexStroke}
              strokeWidth={hexStrokeWidth}
              opacity={hexOpacity}
              style={{
                cursor: onHexClick ? 'pointer' : 'default',
                transition: 'fill 0.2s, stroke 0.2s, opacity 0.2s',
              }}
              onClick={() => handleHexClick(hex.coord)}
              onMouseEnter={(e) => {
                if (onHexClick && !inArc && !inPathPreview) {
                  e.currentTarget.setAttribute('opacity', '0.6');
                }
              }}
              onMouseLeave={(e) => {
                if (!inArc && !inPathPreview) {
                  e.currentTarget.setAttribute('opacity', '0.3');
                }
              }}
            />
            <text
              x={hex.center.x}
              y={hex.center.y}
              textAnchor="middle"
              dominantBaseline="middle"
              fill="#8b7d6b"
              opacity="0.5"
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
        const isReady = readyShips.has(ship.id);
        const isSelectedTarget = ship.id === selectedTargetId;

        return (
          <Ship
            key={ship.id}
            ship={ship}
            layout={layout}
            isSelected={ship.id === selectedShipId}
            onClick={handleShipClick}
            onKeyDown={handleShipKeyDown}
            isValidTarget={isValidTarget}
            isInArc={isInArc}
            isReady={isReady}
            isSelectedTarget={isSelectedTarget}
          />
        );
      })}
    </svg>
  );
}
