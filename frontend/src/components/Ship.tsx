// Ship component for rendering 2-hex ships with facing indicators

import type { Ship as ShipData, Facing } from '../types/game';
import type { HexLayout } from '../types/hex';
import { hexToPixel } from '../types/hex';

interface ShipProps {
  ship: ShipData;
  layout: HexLayout;
  isSelected: boolean;
  onClick: (shipId: string) => void;
  isValidTarget?: boolean;
  isInArc?: boolean;
}

// Calculate a facing arrow for the bow
function getFacingArrowPoints(center: { x: number; y: number }, hexSize: number, facing: Facing): string {
  const angles: Record<Facing, number> = {
    N: -90,
    NE: -45,
    E: 0,
    SE: 45,
    S: 90,
    SW: 135,
    W: 180,
    NW: -135,
  };

  const angle = (angles[facing] * Math.PI) / 180;
  const arrowLength = hexSize * 0.6;
  const arrowWidth = hexSize * 0.3;

  // Arrow tip
  const tipX = center.x + Math.cos(angle) * arrowLength;
  const tipY = center.y + Math.sin(angle) * arrowLength;

  // Arrow base left
  const baseLeftX = center.x + Math.cos(angle - Math.PI / 2) * (arrowWidth / 2);
  const baseLeftY = center.y + Math.sin(angle - Math.PI / 2) * (arrowWidth / 2);

  // Arrow base right
  const baseRightX = center.x + Math.cos(angle + Math.PI / 2) * (arrowWidth / 2);
  const baseRightY = center.y + Math.sin(angle + Math.PI / 2) * (arrowWidth / 2);

  return `${tipX},${tipY} ${baseLeftX},${baseLeftY} ${baseRightX},${baseRightY}`;
}

// Get ship color based on side
function getShipColor(side: string, isSelected: boolean, struck: boolean): string {
  if (struck) {
    return '#666666'; // Gray for struck ships
  }

  const baseColor = side === 'P1' ? '#3b82f6' : '#ef4444'; // Blue for P1, Red for P2

  if (isSelected) {
    return side === 'P1' ? '#60a5fa' : '#f87171'; // Lighter shade when selected
  }

  return baseColor;
}

export function Ship({ ship, layout, isSelected, onClick, isValidTarget = false, isInArc = false }: ShipProps) {
  const bowCenter = hexToPixel(ship.bow_hex, layout);
  const sternCenter = hexToPixel(ship.stern_hex, layout);

  const shipColor = getShipColor(ship.side, isSelected, ship.struck);

  // Determine stroke color and width based on targeting status
  let strokeColor = shipColor;
  let strokeWidth = 2;

  if (isSelected) {
    strokeColor = '#ffffff';
    strokeWidth = 3;
  } else if (isValidTarget) {
    strokeColor = '#4ade80'; // Green for valid targets
    strokeWidth = 4;
  } else if (isInArc) {
    strokeColor = '#fbbf24'; // Yellow for ships in arc but not valid targets
    strokeWidth = 3;
  }

  // Calculate midpoint for ship name
  const midX = (bowCenter.x + sternCenter.x) / 2;
  const midY = (bowCenter.y + sternCenter.y) / 2;

  const facingArrowPoints = getFacingArrowPoints(bowCenter, layout.hexSize, ship.facing);

  return (
    <g
      onClick={(e) => {
        e.stopPropagation();
        onClick(ship.id);
      }}
      style={{ cursor: 'pointer' }}
    >
      {/* Bow hex */}
      <circle
        cx={bowCenter.x}
        cy={bowCenter.y}
        r={layout.hexSize * 0.7}
        fill={shipColor}
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        opacity={0.9}
      />

      {/* Stern hex */}
      <circle
        cx={sternCenter.x}
        cy={sternCenter.y}
        r={layout.hexSize * 0.7}
        fill={shipColor}
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        opacity={0.9}
      />

      {/* Connection line between bow and stern */}
      <line
        x1={bowCenter.x}
        y1={bowCenter.y}
        x2={sternCenter.x}
        y2={sternCenter.y}
        stroke={strokeColor}
        strokeWidth={strokeWidth * 1.5}
        opacity={0.9}
      />

      {/* Facing arrow on bow */}
      <polygon
        points={facingArrowPoints}
        fill="#ffffff"
        stroke="#000000"
        strokeWidth={1}
        opacity={0.9}
      />

      {/* Ship name label */}
      <text
        x={midX}
        y={midY}
        textAnchor="middle"
        dominantBaseline="middle"
        fill="#ffffff"
        fontSize={layout.hexSize * 0.35}
        fontWeight="bold"
        style={{
          pointerEvents: 'none',
          userSelect: 'none',
          textShadow: '1px 1px 2px rgba(0,0,0,0.8)',
        }}
      >
        {ship.name}
      </text>

      {/* Fouled indicator */}
      {ship.fouled && (
        <g>
          <circle
            cx={bowCenter.x + layout.hexSize * 0.5}
            cy={bowCenter.y - layout.hexSize * 0.5}
            r={layout.hexSize * 0.2}
            fill="#ff9800"
            stroke="#000000"
            strokeWidth={1}
          />
          <text
            x={bowCenter.x + layout.hexSize * 0.5}
            y={bowCenter.y - layout.hexSize * 0.5}
            textAnchor="middle"
            dominantBaseline="middle"
            fill="#000000"
            fontSize={layout.hexSize * 0.25}
            fontWeight="bold"
            style={{ pointerEvents: 'none', userSelect: 'none' }}
          >
            F
          </text>
        </g>
      )}

      {/* Struck indicator */}
      {ship.struck && (
        <g>
          <line
            x1={bowCenter.x - layout.hexSize * 0.5}
            y1={bowCenter.y - layout.hexSize * 0.5}
            x2={bowCenter.x + layout.hexSize * 0.5}
            y2={bowCenter.y + layout.hexSize * 0.5}
            stroke="#ff0000"
            strokeWidth={3}
          />
          <line
            x1={bowCenter.x + layout.hexSize * 0.5}
            y1={bowCenter.y - layout.hexSize * 0.5}
            x2={bowCenter.x - layout.hexSize * 0.5}
            y2={bowCenter.y + layout.hexSize * 0.5}
            stroke="#ff0000"
            strokeWidth={3}
          />
        </g>
      )}

      {/* Valid target indicator */}
      {isValidTarget && (
        <g>
          <circle
            cx={bowCenter.x - layout.hexSize * 0.6}
            cy={bowCenter.y - layout.hexSize * 0.6}
            r={layout.hexSize * 0.25}
            fill="#4ade80"
            stroke="#000000"
            strokeWidth={1}
            opacity={0.9}
          />
          <text
            x={bowCenter.x - layout.hexSize * 0.6}
            y={bowCenter.y - layout.hexSize * 0.6}
            textAnchor="middle"
            dominantBaseline="middle"
            fill="#000000"
            fontSize={layout.hexSize * 0.3}
            fontWeight="bold"
            style={{ pointerEvents: 'none', userSelect: 'none' }}
          >
            ✓
          </text>
        </g>
      )}
    </g>
  );
}
