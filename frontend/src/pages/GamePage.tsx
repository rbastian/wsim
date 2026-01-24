// Main game page with board, ship inspector, orders panel, etc.

import { useParams } from "react-router-dom";
import { useState, useEffect, useCallback } from "react";
import { HexGrid } from "../components/HexGrid";
import { TopHUD } from "../components/TopHUD";
import { ShipLogPanel } from "../components/ShipLogPanel";
import { OrdersPanel } from "../components/OrdersPanel";
import { CombatPanel } from "../components/CombatPanel";
import { PhaseControlPanel } from "../components/PhaseControlPanel";
import { EventLog } from "../components/EventLog";
import { api } from "../api/client";
import type { Game, Ship, Broadside, BroadsideArcResponse } from "../types/game";
import { simulateMovementPath, getPathHexes } from "../types/movementPreview";

export function GamePage() {
  const { gameId } = useParams<{ gameId: string }>();
  const [game, setGame] = useState<Game | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedShipId, setSelectedShipId] = useState<string | null>(null);
  const [arcData, setArcData] = useState<BroadsideArcResponse | null>(null);
  const [pathPreviewHexes, setPathPreviewHexes] = useState<[number, number][]>([]);

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

  const handleHexClick = () => {
    // Hex click handling can be implemented later if needed
  };

  const handleShipClick = (shipId: string) => {
    setSelectedShipId(shipId);
    // Clear arc data when selecting a new ship
    setArcData(null);
  };

  const handleGameUpdate = (updatedGame: Game) => {
    setGame(updatedGame);
  };

  const handleBroadsideSelected = useCallback(async (shipId: string, broadside: Broadside) => {
    if (!gameId) return;

    try {
      const arcResponse = await api.getBroadsideArc(gameId, shipId, broadside);
      setArcData(arcResponse);
    } catch (err) {
      console.error("Failed to fetch arc data:", err);
      setArcData(null);
    }
  }, [gameId]);

  const handleClearArc = useCallback(() => {
    setArcData(null);
  }, []);

  const handlePreviewPath = (shipId: string | null, movement: string) => {
    if (!shipId || !movement || !game) {
      setPathPreviewHexes([]);
      return;
    }

    const ship = game.ships[shipId];
    if (!ship) {
      setPathPreviewHexes([]);
      return;
    }

    const path = simulateMovementPath(ship, movement);
    if (path) {
      setPathPreviewHexes(getPathHexes(path));
    } else {
      setPathPreviewHexes([]);
    }
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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* Top HUD with wind rose, turn/phase indicator, and phase action button */}
      <TopHUD game={game} onGameUpdate={handleGameUpdate} />

      {/* Victory Banner */}
      {game.game_ended && (
        <div style={{
          padding: '1.5rem',
          backgroundColor: game.winner === 'P1' ? '#2d5016' : game.winner === 'P2' ? '#501616' : '#3d3d16',
          borderBottom: '3px solid',
          borderColor: game.winner === 'P1' ? '#4a8029' : game.winner === 'P2' ? '#802929' : '#808029',
          textAlign: 'center',
          zIndex: 1001
        }}>
          <h2 style={{
            margin: 0,
            marginBottom: '0.5rem',
            color: '#fff',
            fontSize: '24px',
            fontWeight: 'bold'
          }}>
            {game.winner ? `${game.winner} WINS!` : 'DRAW!'}
          </h2>
          <p style={{ margin: 0, color: '#ddd', fontSize: '14px' }}>
            Game Over
          </p>
        </div>
      )}

      {/* Full-screen hex map ocean container */}
      <div style={{
        flex: 1,
        position: 'relative',
        overflow: 'hidden',
        background: 'radial-gradient(ellipse at center, #1a4d5c 0%, #0d2d3a 100%)'
      }}>
        {/* Wave texture overlay */}
        <div style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='100' height='100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 50 Q 25 40, 50 50 T 100 50' stroke='%23ffffff' stroke-width='0.5' fill='none' opacity='0.1'/%3E%3Cpath d='M0 60 Q 25 50, 50 60 T 100 60' stroke='%23ffffff' stroke-width='0.5' fill='none' opacity='0.1'/%3E%3C/svg%3E")`,
          opacity: 0.1,
          pointerEvents: 'none',
          zIndex: 1
        }} />

        {/* Hex grid - fills remaining space */}
        <div style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'auto',
          padding: '2rem',
          position: 'relative',
          zIndex: 2
        }}>
          <HexGrid
            width={game.map_width}
            height={game.map_height}
            hexSize={25}
            ships={ships}
            selectedShipId={selectedShipId}
            onHexClick={handleHexClick}
            onShipClick={handleShipClick}
            arcHexes={arcData?.arc_hexes}
            shipsInArc={arcData?.ships_in_arc}
            validTargets={arcData?.valid_targets}
            pathPreviewHexes={pathPreviewHexes}
          />
        </div>
      </div>

      {/* Hidden panels - will be moved to ShipActionPanel in next bead */}
      <div style={{ display: 'none' }}>
        <ShipLogPanel ship={selectedShip} />
        <PhaseControlPanel game={game} onGameUpdate={handleGameUpdate} />
        {game.phase === 'planning' && (
          <OrdersPanel
            game={game}
            onGameUpdate={handleGameUpdate}
            onPreviewPath={handlePreviewPath}
          />
        )}
        {game.phase === 'combat' && (
          <CombatPanel
            game={game}
            selectedShipId={selectedShipId}
            onGameUpdate={handleGameUpdate}
            onShipSelect={handleShipClick}
            onBroadsideSelected={handleBroadsideSelected}
            onClearArc={handleClearArc}
            arcData={arcData}
          />
        )}
        <EventLog events={game.event_log} currentTurn={game.turn_number} />
      </div>
    </div>
  );
}
