// Main game page with board, ship inspector, orders panel, etc.

import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";
import { HexGrid } from "../components/HexGrid";
import { ShipLogPanel } from "../components/ShipLogPanel";
import { OrdersPanel } from "../components/OrdersPanel";
import { api } from "../api/client";
import type { HexCoordinate } from "../types/hex";
import type { Game, Ship } from "../types/game";

export function GamePage() {
  const { gameId } = useParams<{ gameId: string }>();
  const [game, setGame] = useState<Game | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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

  const handleHexClick = (_hex: HexCoordinate) => {
    // Hex click handling can be implemented later if needed
  };

  const handleShipClick = (shipId: string) => {
    setSelectedShipId(shipId);
  };

  const handleGameUpdate = (updatedGame: Game) => {
    setGame(updatedGame);
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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#0a0a0a' }}>
      {/* Header */}
      <div style={{
        padding: '1rem',
        borderBottom: '2px solid #333',
        backgroundColor: '#1a1a1a'
      }}>
        <h1 style={{ margin: 0, marginBottom: '0.5rem', color: '#fff' }}>
          {game.scenario_id.replace(/_/g, ' ').toUpperCase()}
        </h1>
        <p style={{ margin: 0, color: '#888', fontSize: '14px' }}>
          Turn {game.turn_number} | Phase: <span style={{ color: '#4a90e2', fontWeight: 'bold' }}>{game.phase.toUpperCase()}</span> | Wind: {game.wind_direction}
        </p>
      </div>

      {/* Main content area */}
      <div style={{
        flex: 1,
        display: 'flex',
        overflow: 'hidden',
        padding: '1rem',
        gap: '1rem'
      }}>
        {/* Left panel - Ship Log */}
        <div style={{
          width: '320px',
          flexShrink: 0,
          display: 'flex',
          flexDirection: 'column',
          minHeight: 0
        }}>
          <ShipLogPanel ship={selectedShip} />
        </div>

        {/* Center - Hex Grid Board */}
        <div style={{
          flex: 1,
          minHeight: 0,
          overflow: 'auto',
          backgroundColor: '#1a1a1a',
          borderRadius: '8px',
          padding: '1rem'
        }}>
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

        {/* Right panel - Orders/Combat panels */}
        <div style={{
          width: '320px',
          flexShrink: 0,
          display: 'flex',
          flexDirection: 'column',
          minHeight: 0
        }}>
          <OrdersPanel game={game} onGameUpdate={handleGameUpdate} />
        </div>
      </div>
    </div>
  );
}
