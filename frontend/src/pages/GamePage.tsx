// Main game page with board, ship inspector, orders panel, etc.

import { useParams } from "react-router-dom";
import { useState, useEffect, useCallback } from "react";
import { HexGrid } from "../components/HexGrid";
import { TopHUD } from "../components/TopHUD";
import { ShipActionPanel } from "../components/ShipActionPanel";
import { PlanningControls } from "../components/PlanningControls";
import { CombatControls } from "../components/CombatControls";
import { ShipLogPanel } from "../components/ShipLogPanel";
import { OrdersPanel } from "../components/OrdersPanel";
import { CombatPanel } from "../components/CombatPanel";
import { PhaseControlPanel } from "../components/PhaseControlPanel";
import { EventLog } from "../components/EventLog";
import { ScreenReaderLiveRegion } from "../components/ScreenReaderLiveRegion";
import { SkipLinks } from "../components/SkipLinks";
import { api } from "../api/client";
import type { Game, Ship, Broadside, BroadsideArcResponse } from "../types/game";
import { simulateMovementPath, getPathHexes } from "../types/movementPreview";
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts";
import { useScreenReader } from "../hooks/useScreenReader";

export function GamePage() {
  const { gameId } = useParams<{ gameId: string }>();
  const [game, setGame] = useState<Game | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedShipId, setSelectedShipId] = useState<string | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [arcData, setArcData] = useState<BroadsideArcResponse | null>(null);
  const [pathPreviewHexes, setPathPreviewHexes] = useState<[number, number][]>([]);
  const [selectedTargetId, setSelectedTargetId] = useState<string | null>(null);
  // Track which ships have submitted orders and marked ready
  const [shipReadyState, setShipReadyState] = useState<Map<string, boolean>>(new Map());

  // Screen reader announcements
  const { announce } = useScreenReader();

  // Keyboard shortcuts
  useKeyboardShortcuts({
    shortcuts: [
      {
        key: "Escape",
        description: "Close ship action panel",
        action: () => {
          if (isPanelOpen) {
            handlePanelClose();
            announce("Ship action panel closed", "polite");
          }
        },
      },
      {
        key: "?",
        shift: true,
        description: "Show keyboard shortcuts help",
        action: () => {
          announce(
            "Keyboard shortcuts: Escape to close panel, Tab to navigate, Enter or Space to select ships, Arrow keys to navigate between ships, Question mark for help",
            "polite"
          );
        },
      },
      {
        key: "h",
        description: "Focus on TopHUD",
        action: () => {
          const hud = document.querySelector(".top-hud") as HTMLElement;
          if (hud) {
            hud.focus();
            announce("Focused on game controls", "polite");
          }
        },
      },
      {
        key: "m",
        description: "Focus on hex map",
        action: () => {
          const map = document.querySelector(".hex-map-container") as HTMLElement;
          if (map) {
            const firstShip = document.querySelector('[role="button"][aria-pressed]') as HTMLElement;
            if (firstShip) {
              firstShip.focus();
              announce("Focused on hex map", "polite");
            }
          }
        },
      },
    ],
    enabled: !!game && !game.game_ended,
  });

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

  // Update ship ready state when game state changes
  useEffect(() => {
    if (!game) return;

    const newReadyState = new Map<string, boolean>();

    // Check P1 ships
    if (game.p1_orders && game.p1_orders.ready) {
      game.p1_orders.orders.forEach(order => {
        newReadyState.set(order.ship_id, true);
      });
    }

    // Check P2 ships
    if (game.p2_orders && game.p2_orders.ready) {
      game.p2_orders.orders.forEach(order => {
        newReadyState.set(order.ship_id, true);
      });
    }

    setShipReadyState(newReadyState);
  }, [game]);

  const handleHexClick = () => {
    // Hex click handling can be implemented later if needed
  };

  const handleShipClick = (shipId: string) => {
    setSelectedShipId(shipId);
    setIsPanelOpen(true);
    // Clear arc data when selecting a new ship
    setArcData(null);

    // Announce ship selection to screen readers
    if (game) {
      const ship = game.ships[shipId];
      if (ship) {
        announce(
          `Selected ${ship.name}, ${ship.side}. Hull ${ship.hull}, Rigging ${ship.rigging}, Crew ${ship.crew}.`,
          "polite"
        );
      }
    }
  };

  const handlePanelClose = () => {
    setIsPanelOpen(false);
    // Clear selection after a short delay to allow for animation
    setTimeout(() => {
      setSelectedShipId(null);
      setArcData(null);
    }, 300);
  };

  const handleGameUpdate = (updatedGame: Game) => {
    // Announce phase changes
    if (game && game.phase !== updatedGame.phase) {
      const phaseNames: Record<string, string> = {
        planning: "Planning Phase",
        movement: "Movement Phase",
        combat: "Combat Phase",
        reload: "Reload Phase",
      };
      announce(`Phase changed to ${phaseNames[updatedGame.phase] || updatedGame.phase}`, "assertive");
    }

    // Announce turn changes
    if (game && game.turn_number !== updatedGame.turn_number) {
      announce(`Advanced to Turn ${updatedGame.turn_number}`, "assertive");
    }

    // Announce game end
    if (updatedGame.game_ended && (!game || !game.game_ended)) {
      const winnerText = updatedGame.winner ? `${updatedGame.winner} wins!` : "Game ended in a draw!";
      announce(winnerText, "assertive");
    }

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
    setSelectedTargetId(null);
  }, []);

  const handleTargetSelected = useCallback((targetId: string | null) => {
    setSelectedTargetId(targetId);
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
      {/* Screen reader live regions and skip links */}
      <ScreenReaderLiveRegion />
      <SkipLinks />

      {/* Top HUD with wind rose, turn/phase indicator, and phase action button */}
      <TopHUD game={game} onGameUpdate={handleGameUpdate} shipReadyState={shipReadyState} />

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
      <main
        id="main-content"
        role="main"
        aria-label="Game battlefield"
        style={{
          flex: 1,
          position: 'relative',
          overflow: 'hidden',
          background: 'radial-gradient(ellipse at center, #1a4d5c 0%, #0d2d3a 100%)'
        }}
      >
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
        <div className="hex-map-container" style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'auto',
          padding: '2rem',
          zIndex: 2,
          boxSizing: 'border-box'
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
            selectedTargetId={selectedTargetId}
            pathPreviewHexes={pathPreviewHexes}
            readyShips={new Set(Array.from(shipReadyState.keys()).filter(id => shipReadyState.get(id)))}
          />
        </div>
      </main>

      {/* Ship Action Panel - slides in from right */}
      <ShipActionPanel
        id="ship-actions"
        isOpen={isPanelOpen}
        selectedShip={selectedShip}
        game={game}
        onClose={handlePanelClose}
        isReady={selectedShip ? shipReadyState.get(selectedShip.id) || false : false}
      >
        {/* Phase-specific controls */}
        {game.phase === 'planning' && selectedShip && (
          <PlanningControls
            ship={selectedShip}
            game={game}
            onGameUpdate={handleGameUpdate}
            onPreviewPath={handlePreviewPath}
          />
        )}

        {game.phase === 'combat' && selectedShip && (
          <CombatControls
            ship={selectedShip}
            game={game}
            onGameUpdate={handleGameUpdate}
            onBroadsideSelected={handleBroadsideSelected}
            onClearArc={handleClearArc}
            onTargetSelected={handleTargetSelected}
            arcData={arcData}
          />
        )}

        {/* Temporarily hide old panels - will be migrated in future beads */}
        <div style={{ display: 'none' }}>
          <ShipLogPanel ship={selectedShip} />
          <PhaseControlPanel game={game} onGameUpdate={handleGameUpdate} />
          <OrdersPanel
            game={game}
            onGameUpdate={handleGameUpdate}
            onPreviewPath={handlePreviewPath}
          />
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
      </ShipActionPanel>
    </div>
  );
}
