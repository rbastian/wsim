// Main game page with board, ship inspector, orders panel, etc.

import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import { HexGrid } from "../components/HexGrid";
import { api } from "../api/client";
import type { HexCoordinate } from "../types/hex";
import type { Game, Ship } from "../types/game";

export function GamePage() {
  const { gameId } = useParams<{ gameId: string }>();
  const [game, setGame] = useState<Game | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedHex, setSelectedHex] = useState<HexCoordinate | null>(null);
  const [selectedShipId, setSelectedShipId] = useState<string | null>(null);

  // Fetch game state on mount
  useEffect(() => {
    if (!gameId) {
      setError("No game ID provided");
      setLoading(false);
      return;
    }

    const fetchGame = async () => {
      try {
        setLoading(true);
        setError(null);
        const gameData = await api.getGame(gameId);
        setGame(gameData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load game");
        console.error("Failed to load game:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchGame();
  }, [gameId]);

  const handleHexClick = (hex: HexCoordinate) => {
    setSelectedHex(hex);
    console.log('Hex clicked:', hex);
  };

  const handleShipClick = (shipId: string) => {
    setSelectedShipId(shipId);
    console.log('Ship clicked:', shipId);
  };

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <p>Loading game...</p>
      </div>
    );
  }

  if (error || !game) {
    return (
      <div style={{ padding: '2rem' }}>
        <h1>Error</h1>
        <p style={{ color: 'red' }}>{error || "Failed to load game"}</p>
      </div>
    );
  }

  // Convert ships record to array
  const ships: Ship[] = Object.values(game.ships);
  const selectedShip = selectedShipId ? game.ships[selectedShipId] : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', padding: '1rem' }}>
      <div style={{ marginBottom: '1rem' }}>
        <h1 style={{ margin: 0, marginBottom: '0.5rem' }}>
          Game: {game.scenario_id} (Turn {game.turn_number})
        </h1>
        <p style={{ margin: 0, color: '#888' }}>
          Phase: {game.phase} | Wind: {game.wind_direction}
        </p>
        {selectedHex && (
          <p style={{ margin: 0, color: '#888' }}>
            Selected hex: [{selectedHex.col}, {selectedHex.row}]
          </p>
        )}
        {selectedShip && (
          <p style={{ margin: 0, color: '#4a90e2' }}>
            Selected ship: {selectedShip.name} ({selectedShip.side}) |
            Hull: {selectedShip.hull} | Rigging: {selectedShip.rigging} |
            Crew: {selectedShip.crew} | Marines: {selectedShip.marines}
            {selectedShip.fouled && " | FOULED"}
            {selectedShip.struck && " | STRUCK"}
          </p>
        )}
      </div>
      <div style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>
        <HexGrid
          width={game.map_width}
          height={game.map_height}
          hexSize={25}
          ships={ships}
          selectedShipId={selectedShipId}
          onHexClick={handleHexClick}
          onShipClick={handleShipClick}
        />
      </div>
    </div>
  );
}
