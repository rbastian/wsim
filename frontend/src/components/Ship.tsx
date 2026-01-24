// Ship component for rendering 2-hex ships with facing indicators

import { useState } from 'react';
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
  isReady?: boolean;
  isSelectedTarget?: boolean;
  onKeyDown?: (e: React.KeyboardEvent, shipId: string) => void;
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

// Get ship color based on side and state
function getShipColor(side: string, struck: boolean): string {
  if (struck) {
    return '#6a6a6a'; // --struck-gray
  }

  // Player colors based on UX redesign
  return side === 'P1' ? '#3a5ba7' : '#a73a3a'; // --player-1 / --player-2
}

// Get stroke color and width based on ship state
function getStrokeStyle(
  ship: ShipData,
  isSelected: boolean,
  isReady: boolean,
  isValidTarget: boolean,
  isInArc: boolean
): { color: string; width: number; dashArray?: string } {
  // Selection takes priority
  if (isSelected) {
    return { color: '#f4d03f', width: 4 }; // --selected-glow
  }

  // Ready state
  if (isReady && !ship.struck) {
    return { color: '#4a8f4a', width: 3 }; // --ready-green
  }

  // Struck ships have dashed border
  if (ship.struck) {
    return { color: '#6a6a6a', width: 2, dashArray: '4 4' }; // --struck-gray
  }

  // Fouled state
  if (ship.fouled) {
    return { color: '#d4874f', width: 3 }; // --fouled-orange
  }

  // Valid target - red pulsing outline (combat theme)
  if (isValidTarget) {
    return { color: '#a74a4a', width: 4 }; // Combat red for valid targets
  }

  // In arc but not valid
  if (isInArc) {
    return { color: '#fbbf24', width: 3 }; // Yellow
  }

  // Default: darker shade of ship color
  const baseColor = ship.side === 'P1' ? '#2a4887' : '#872a2a';
  return { color: baseColor, width: 2 };
}

export function Ship({
  ship,
  layout,
  isSelected,
  onClick,
  isValidTarget = false,
  isInArc = false,
  isReady = false,
  isSelectedTarget = false,
  onKeyDown,
}: ShipProps) {
  const bowCenter = hexToPixel(ship.bow_hex, layout);
  const sternCenter = hexToPixel(ship.stern_hex, layout);

  const shipColor = getShipColor(ship.side, ship.struck);
  const strokeStyle = getStrokeStyle(ship, isSelected, isReady, isValidTarget, isInArc);

  // Calculate midpoint for ship name
  const midX = (bowCenter.x + sternCenter.x) / 2;
  const midY = (bowCenter.y + sternCenter.y) / 2;

  const facingArrowPoints = getFacingArrowPoints(bowCenter, layout.hexSize, ship.facing);

  // Opacity: struck ships are semi-transparent, hovered ships are fully opaque
  const [isHovered, setIsHovered] = useState(false);
  const [justSelected, setJustSelected] = useState(false);

  const baseOpacity = ship.struck ? 0.4 : 0.85;
  const opacity = isHovered && !ship.struck ? 1 : baseOpacity;

  // Enhanced stroke width on hover
  const hoverStrokeWidth = isHovered && !isSelected ? strokeStyle.width + 0.5 : strokeStyle.width;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onClick(ship.id);

    // Trigger selection animation
    setJustSelected(true);
    setTimeout(() => setJustSelected(false), 300);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick(ship.id);
      setJustSelected(true);
      setTimeout(() => setJustSelected(false), 300);
    }

    if (onKeyDown) {
      onKeyDown(e, ship.id);
    }
  };

  return (
    <g
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      tabIndex={0}
      role="button"
      aria-label={`${ship.name}, ${ship.side}, Hull ${ship.hull}, ${isReady ? 'Ready' : 'Not ready'}`}
      aria-pressed={isSelected}
      style={{
        cursor: 'pointer',
        transition: 'all 0.15s ease-out',
      }}
      className={justSelected ? 'ship-just-selected' : ''}
    >
      {/* Glow effect for selected ships */}
      {isSelected && (
        <>
          <circle
            cx={bowCenter.x}
            cy={bowCenter.y}
            r={layout.hexSize * 0.7}
            fill="none"
            stroke={strokeStyle.color}
            strokeWidth={strokeStyle.width + 2}
            opacity={0.3}
            filter="blur(8px)"
          />
          <circle
            cx={sternCenter.x}
            cy={sternCenter.y}
            r={layout.hexSize * 0.7}
            fill="none"
            stroke={strokeStyle.color}
            strokeWidth={strokeStyle.width + 2}
            opacity={0.3}
            filter="blur(8px)"
          />
        </>
      )}

      {/* Bow hex */}
      <circle
        cx={bowCenter.x}
        cy={bowCenter.y}
        r={layout.hexSize * 0.7}
        fill={shipColor}
        stroke={strokeStyle.color}
        strokeWidth={hoverStrokeWidth}
        strokeDasharray={strokeStyle.dashArray}
        opacity={opacity}
        style={{ transition: 'stroke-width 0.15s ease-out, opacity 0.15s ease-out' }}
      >
        {/* Pulsing animation for ready ships */}
        {isReady && !ship.struck && (
          <animate attributeName="opacity" values="0.85;1;0.85" dur="2s" repeatCount="indefinite" />
        )}
        {/* Pulsing animation for valid combat targets */}
        {isValidTarget && (
          <animate attributeName="stroke-width" values={`${hoverStrokeWidth};${hoverStrokeWidth + 2};${hoverStrokeWidth}`} dur="1.5s" repeatCount="indefinite" />
        )}
      </circle>

      {/* Stern hex */}
      <circle
        cx={sternCenter.x}
        cy={sternCenter.y}
        r={layout.hexSize * 0.7}
        fill={shipColor}
        stroke={strokeStyle.color}
        strokeWidth={hoverStrokeWidth}
        strokeDasharray={strokeStyle.dashArray}
        opacity={opacity}
        style={{ transition: 'stroke-width 0.15s ease-out, opacity 0.15s ease-out' }}
      >
        {/* Pulsing animation for ready ships */}
        {isReady && !ship.struck && (
          <animate attributeName="opacity" values="0.85;1;0.85" dur="2s" repeatCount="indefinite" />
        )}
        {/* Pulsing animation for valid combat targets */}
        {isValidTarget && (
          <animate attributeName="stroke-width" values={`${hoverStrokeWidth};${hoverStrokeWidth + 2};${hoverStrokeWidth}`} dur="1.5s" repeatCount="indefinite" />
        )}
      </circle>

      {/* Connection line between bow and stern */}
      <line
        x1={bowCenter.x}
        y1={bowCenter.y}
        x2={sternCenter.x}
        y2={sternCenter.y}
        stroke={strokeStyle.color}
        strokeWidth={hoverStrokeWidth * 1.5}
        strokeDasharray={strokeStyle.dashArray}
        opacity={opacity}
        style={{ transition: 'stroke-width 0.15s ease-out, opacity 0.15s ease-out' }}
      >
        {/* Pulsing animation for valid combat targets */}
        {isValidTarget && (
          <animate attributeName="stroke-width" values={`${hoverStrokeWidth * 1.5};${(hoverStrokeWidth + 2) * 1.5};${hoverStrokeWidth * 1.5}`} dur="1.5s" repeatCount="indefinite" />
        )}
      </line>

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

      {/* Ready badge - checkmark at stern */}
      {isReady && !ship.struck && (
        <g>
          <circle
            cx={sternCenter.x}
            cy={sternCenter.y - layout.hexSize * 0.8}
            r={layout.hexSize * 0.25}
            fill="#4a8f4a"
            stroke="#ffffff"
            strokeWidth={2}
            opacity={0.95}
          />
          {/* Checkmark path */}
          <path
            d={`M ${sternCenter.x - layout.hexSize * 0.15} ${sternCenter.y - layout.hexSize * 0.8}
                L ${sternCenter.x - layout.hexSize * 0.05} ${sternCenter.y - layout.hexSize * 0.7}
                L ${sternCenter.x + layout.hexSize * 0.15} ${sternCenter.y - layout.hexSize * 0.9}`}
            stroke="#ffffff"
            strokeWidth={2.5}
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
        </g>
      )}

      {/* Struck overlay - X across both hexes */}
      {ship.struck && (
        <g>
          {/* X overlay across ship */}
          <line
            x1={bowCenter.x - layout.hexSize * 0.6}
            y1={bowCenter.y - layout.hexSize * 0.6}
            x2={sternCenter.x + layout.hexSize * 0.6}
            y2={sternCenter.y + layout.hexSize * 0.6}
            stroke="#5a4a3a"
            strokeWidth={3}
            opacity={0.6}
          />
          <line
            x1={bowCenter.x + layout.hexSize * 0.6}
            y1={bowCenter.y - layout.hexSize * 0.6}
            x2={sternCenter.x - layout.hexSize * 0.6}
            y2={sternCenter.y + layout.hexSize * 0.6}
            stroke="#5a4a3a"
            strokeWidth={3}
            opacity={0.6}
          />
        </g>
      )}

      {/* Fouled badge - chain link icon */}
      {ship.fouled && !ship.struck && (
        <g>
          <circle
            cx={bowCenter.x + layout.hexSize * 0.7}
            cy={bowCenter.y - layout.hexSize * 0.7}
            r={layout.hexSize * 0.25}
            fill="#d4874f"
            stroke="#ffffff"
            strokeWidth={2}
            opacity={0.95}
          />
          {/* Chain link icon - two interlocking circles */}
          <circle
            cx={bowCenter.x + layout.hexSize * 0.65}
            cy={bowCenter.y - layout.hexSize * 0.7}
            r={layout.hexSize * 0.1}
            fill="none"
            stroke="#ffffff"
            strokeWidth={2}
          />
          <circle
            cx={bowCenter.x + layout.hexSize * 0.75}
            cy={bowCenter.y - layout.hexSize * 0.7}
            r={layout.hexSize * 0.1}
            fill="none"
            stroke="#ffffff"
            strokeWidth={2}
          />
        </g>
      )}

      {/* Valid target indicator - removed as pulsing red outline is sufficient */}

      {/* Selected target crosshairs */}
      {isSelectedTarget && (
        <g>
          {/* Crosshairs on bow */}
          <g>
            {/* Horizontal line */}
            <line
              x1={bowCenter.x - layout.hexSize * 0.6}
              y1={bowCenter.y}
              x2={bowCenter.x + layout.hexSize * 0.6}
              y2={bowCenter.y}
              stroke="#f4d03f"
              strokeWidth={3}
              opacity={0.9}
            />
            {/* Vertical line */}
            <line
              x1={bowCenter.x}
              y1={bowCenter.y - layout.hexSize * 0.6}
              x2={bowCenter.x}
              y2={bowCenter.y + layout.hexSize * 0.6}
              stroke="#f4d03f"
              strokeWidth={3}
              opacity={0.9}
            />
            {/* Center circle */}
            <circle
              cx={bowCenter.x}
              cy={bowCenter.y}
              r={layout.hexSize * 0.15}
              fill="none"
              stroke="#f4d03f"
              strokeWidth={3}
              opacity={0.9}
            />
            {/* Pulsing animation */}
            <circle
              cx={bowCenter.x}
              cy={bowCenter.y}
              r={layout.hexSize * 0.5}
              fill="none"
              stroke="#f4d03f"
              strokeWidth={2}
              opacity={0.6}
            >
              <animate
                attributeName="r"
                values={`${layout.hexSize * 0.3};${layout.hexSize * 0.6};${layout.hexSize * 0.3}`}
                dur="2s"
                repeatCount="indefinite"
              />
              <animate
                attributeName="opacity"
                values="0.6;0.1;0.6"
                dur="2s"
                repeatCount="indefinite"
              />
            </circle>
          </g>

          {/* Crosshairs on stern */}
          <g>
            {/* Horizontal line */}
            <line
              x1={sternCenter.x - layout.hexSize * 0.6}
              y1={sternCenter.y}
              x2={sternCenter.x + layout.hexSize * 0.6}
              y2={sternCenter.y}
              stroke="#f4d03f"
              strokeWidth={3}
              opacity={0.9}
            />
            {/* Vertical line */}
            <line
              x1={sternCenter.x}
              y1={sternCenter.y - layout.hexSize * 0.6}
              x2={sternCenter.x}
              y2={sternCenter.y + layout.hexSize * 0.6}
              stroke="#f4d03f"
              strokeWidth={3}
              opacity={0.9}
            />
            {/* Center circle */}
            <circle
              cx={sternCenter.x}
              cy={sternCenter.y}
              r={layout.hexSize * 0.15}
              fill="none"
              stroke="#f4d03f"
              strokeWidth={3}
              opacity={0.9}
            />
            {/* Pulsing animation */}
            <circle
              cx={sternCenter.x}
              cy={sternCenter.y}
              r={layout.hexSize * 0.5}
              fill="none"
              stroke="#f4d03f"
              strokeWidth={2}
              opacity={0.6}
            >
              <animate
                attributeName="r"
                values={`${layout.hexSize * 0.3};${layout.hexSize * 0.6};${layout.hexSize * 0.3}`}
                dur="2s"
                repeatCount="indefinite"
              />
              <animate
                attributeName="opacity"
                values="0.6;0.1;0.6"
                dur="2s"
                repeatCount="indefinite"
              />
            </circle>
          </g>
        </g>
      )}
    </g>
  );
}
