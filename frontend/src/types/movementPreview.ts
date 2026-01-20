// Movement preview utilities
// Simulates ship movement to show predicted path on hex board

import type { Ship, Facing } from './game';
import type { HexCoordinate } from './hex';

export interface PathStep {
  bow: HexCoordinate;
  stern: HexCoordinate;
  facing: Facing;
  actionType: 'turn_left' | 'turn_right' | 'move_forward' | 'no_movement';
}

export interface MovementPath {
  steps: PathStep[];
  finalPosition: PathStep;
}

// Turn left (counter-clockwise 60 degrees)
function turnLeft(facing: Facing): Facing {
  const rotationMap: Record<Facing, Facing> = {
    N: 'NW',
    NE: 'N',
    E: 'NE',
    SE: 'E',
    S: 'SE',
    SW: 'S',
    W: 'SW',
    NW: 'W',
  };
  return rotationMap[facing];
}

// Turn right (clockwise 60 degrees)
function turnRight(facing: Facing): Facing {
  const rotationMap: Record<Facing, Facing> = {
    N: 'NE',
    NE: 'E',
    E: 'SE',
    SE: 'S',
    S: 'SW',
    SW: 'W',
    W: 'NW',
    NW: 'N',
  };
  return rotationMap[facing];
}

// Get adjacent hex in given direction (odd-q vertical layout)
function getAdjacentHex(hex: HexCoordinate, direction: Facing): HexCoordinate {
  const isOddCol = hex.col % 2 === 1;

  // Direction offsets for odd-q vertical layout
  // Format: [col_offset, row_offset_even_col, row_offset_odd_col]
  const directionOffsets: Record<Facing, [number, number, number]> = {
    N: [0, -1, -1],
    NE: [1, -1, 0],
    SE: [1, 0, 1],
    S: [0, 1, 1],
    SW: [-1, 0, 1],
    NW: [-1, -1, 0],
    E: [1, 0, 0],
    W: [-1, 0, 0],
  };

  const [colOffset, rowOffsetEven, rowOffsetOdd] = directionOffsets[direction];
  const rowOffset = isOddCol ? rowOffsetOdd : rowOffsetEven;

  return {
    col: hex.col + colOffset,
    row: hex.row + rowOffset,
  };
}

// Calculate stern hex from bow and facing
function calculateStern(bow: HexCoordinate, facing: Facing): HexCoordinate {
  const oppositeFacing: Record<Facing, Facing> = {
    N: 'S',
    NE: 'SW',
    E: 'W',
    SE: 'NW',
    S: 'N',
    SW: 'NE',
    W: 'E',
    NW: 'SE',
  };

  return getAdjacentHex(bow, oppositeFacing[facing]);
}

// Parse movement string and simulate path
export function simulateMovementPath(
  ship: Ship,
  movementString: string,
  maxSteps: number = 20
): MovementPath | null {
  // Validate movement string
  const normalized = movementString.trim().toUpperCase();
  if (!normalized) return null;

  // Special case: '0' means no movement
  if (normalized === '0') {
    const finalPosition: PathStep = {
      bow: { col: ship.bow_hex.col, row: ship.bow_hex.row },
      stern: { col: ship.stern_hex.col, row: ship.stern_hex.row },
      facing: ship.facing,
      actionType: 'no_movement',
    };
    return {
      steps: [finalPosition],
      finalPosition,
    };
  }

  // Validate characters
  for (let i = 0; i < normalized.length; i++) {
    const char = normalized[i];
    if (char !== 'L' && char !== 'R' && !/[1-9]/.test(char)) {
      return null; // Invalid character
    }
  }

  // Start simulation
  const steps: PathStep[] = [];
  let currentBow: HexCoordinate = { col: ship.bow_hex.col, row: ship.bow_hex.row };
  let currentStern: HexCoordinate = { col: ship.stern_hex.col, row: ship.stern_hex.row };
  let currentFacing: Facing = ship.facing;

  // Execute each character in the movement string
  for (let i = 0; i < normalized.length && steps.length < maxSteps; i++) {
    const char = normalized[i];

    if (char === 'L') {
      // Turn left
      currentFacing = turnLeft(currentFacing);
      currentStern = calculateStern(currentBow, currentFacing);
      steps.push({
        bow: { ...currentBow },
        stern: { ...currentStern },
        facing: currentFacing,
        actionType: 'turn_left',
      });
    } else if (char === 'R') {
      // Turn right
      currentFacing = turnRight(currentFacing);
      currentStern = calculateStern(currentBow, currentFacing);
      steps.push({
        bow: { ...currentBow },
        stern: { ...currentStern },
        facing: currentFacing,
        actionType: 'turn_right',
      });
    } else if (/[1-9]/.test(char)) {
      // Move forward N hexes
      const distance = parseInt(char, 10);
      for (let j = 0; j < distance && steps.length < maxSteps; j++) {
        currentBow = getAdjacentHex(currentBow, currentFacing);
        currentStern = calculateStern(currentBow, currentFacing);
        steps.push({
          bow: { ...currentBow },
          stern: { ...currentStern },
          facing: currentFacing,
          actionType: 'move_forward',
        });
      }
    }
  }

  if (steps.length === 0) return null;

  return {
    steps,
    finalPosition: steps[steps.length - 1],
  };
}

// Extract all hexes from path for visualization
export function getPathHexes(path: MovementPath | null): [number, number][] {
  if (!path) return [];

  const hexSet = new Set<string>();

  for (const step of path.steps) {
    hexSet.add(`${step.bow.col},${step.bow.row}`);
    hexSet.add(`${step.stern.col},${step.stern.row}`);
  }

  return Array.from(hexSet).map((key) => {
    const [col, row] = key.split(',').map(Number);
    return [col, row] as [number, number];
  });
}
