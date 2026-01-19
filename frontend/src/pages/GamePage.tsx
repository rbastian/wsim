// Main game page with board, ship inspector, orders panel, etc.

import { useParams } from "react-router-dom";
import { useState } from "react";
import { HexGrid } from "../components/HexGrid";
import type { HexCoordinate } from "../types/hex";

export function GamePage() {
  const { gameId } = useParams<{ gameId: string }>();
  const [selectedHex, setSelectedHex] = useState<HexCoordinate | null>(null);

  // Default to Frigate Duel scenario dimensions (25x20)
  const mapWidth = 25;
  const mapHeight = 20;

  const handleHexClick = (hex: HexCoordinate) => {
    setSelectedHex(hex);
    console.log('Hex clicked:', hex);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', padding: '1rem' }}>
      <div style={{ marginBottom: '1rem' }}>
        <h1 style={{ margin: 0, marginBottom: '0.5rem' }}>Game: {gameId}</h1>
        {selectedHex && (
          <p style={{ margin: 0, color: '#888' }}>
            Selected hex: [{selectedHex.col}, {selectedHex.row}]
          </p>
        )}
      </div>
      <div style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
        <HexGrid
          width={mapWidth}
          height={mapHeight}
          hexSize={25}
          onHexClick={handleHexClick}
        />
      </div>
    </div>
  );
}
