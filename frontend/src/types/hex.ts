// Hex coordinate types and utilities
// Using axial/offset coordinates for the hex grid

export interface HexCoordinate {
  col: number;
  row: number;
}

export interface HexPixel {
  x: number;
  y: number;
}

export interface HexLayout {
  hexSize: number;
  origin: HexPixel;
  orientation: 'flat' | 'pointy';
}

// Convert hex coordinate to pixel position for flat-top hexagons
export function hexToPixel(hex: HexCoordinate, layout: HexLayout): HexPixel {
  const { hexSize, origin } = layout;

  // Using offset coordinates (odd-r layout)
  // For flat-top hexes:
  const x = hexSize * (3/2) * hex.col;
  const y = hexSize * Math.sqrt(3) * (hex.row + 0.5 * (hex.col & 1));

  return {
    x: x + origin.x,
    y: y + origin.y
  };
}

// Get the six corner points of a hex for SVG polygon
export function getHexCorners(center: HexPixel, hexSize: number): HexPixel[] {
  const corners: HexPixel[] = [];

  // Flat-top hex corners, starting from right and going clockwise
  for (let i = 0; i < 6; i++) {
    const angle = Math.PI / 3 * i;
    corners.push({
      x: center.x + hexSize * Math.cos(angle),
      y: center.y + hexSize * Math.sin(angle)
    });
  }

  return corners;
}

// Convert corners array to SVG points string
export function cornersToPoints(corners: HexPixel[]): string {
  return corners.map(c => `${c.x},${c.y}`).join(' ');
}
