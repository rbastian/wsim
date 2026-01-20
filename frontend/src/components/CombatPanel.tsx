// Combat panel for the combat phase
// Allows players to fire broadsides at legal targets with closest-target rule enforcement

import { useState, useEffect } from "react";
import type { Game, Ship, Broadside, AimPoint, EventLogEntry } from "../types/game";
import { api } from "../api/client";

interface CombatPanelProps {
  game: Game;
  selectedShipId: string | null;
  onGameUpdate: (game: Game) => void;
  onShipSelect: (shipId: string) => void;
  onBroadsideSelected: (shipId: string, broadside: Broadside) => void;
  onClearArc: () => void;
}

// Helper function to determine if a broadside is loaded
function isBroadsideLoaded(ship: Ship, broadside: Broadside): boolean {
  const loadState = broadside === "L" ? ship.load_L : ship.load_R;
  return loadState === "R"; // R = Roundshot (loaded)
}

// Helper function to check if ship can fire
function canShipFire(ship: Ship): boolean {
  return !ship.struck && (isBroadsideLoaded(ship, "L") || isBroadsideLoaded(ship, "R"));
}

// Helper function to get target info for display
interface TargetInfo {
  ship: Ship;
  distance: number;
  isClosest: boolean;
}

// Calculate distance between two hex coordinates
function hexDistance(a: { col: number; row: number }, b: { col: number; row: number }): number {
  // Convert offset coordinates to cube coordinates for distance calculation
  const axialA = { q: a.col - Math.floor(a.row / 2), r: a.row };
  const axialB = { q: b.col - Math.floor(b.row / 2), r: b.row };

  return (Math.abs(axialA.q - axialB.q) +
          Math.abs(axialA.q + axialA.r - axialB.q - axialB.r) +
          Math.abs(axialA.r - axialB.r)) / 2;
}

// Get potential targets (enemies not struck, in arc)
// This is a simplified client-side calculation - server enforces closest-target rule
function getPotentialTargets(firingShip: Ship, allShips: Ship[]): TargetInfo[] {
  const enemies = allShips.filter(
    (ship) => ship.side !== firingShip.side && !ship.struck
  );

  // Calculate distances (simplified - using bow hex only)
  const targets: TargetInfo[] = enemies.map((enemy) => ({
    ship: enemy,
    distance: hexDistance(firingShip.bow_hex, enemy.bow_hex),
    isClosest: false,
  }));

  // Mark closest targets
  if (targets.length > 0) {
    const minDistance = Math.min(...targets.map((t) => t.distance));
    targets.forEach((t) => {
      t.isClosest = t.distance === minDistance;
    });
  }

  return targets.sort((a, b) => a.distance - b.distance);
}

export function CombatPanel({ game, selectedShipId, onGameUpdate, onShipSelect, onBroadsideSelected, onClearArc }: CombatPanelProps) {
  const [selectedBroadside, setSelectedBroadside] = useState<Broadside | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<string | null>(null);
  const [selectedAim, setSelectedAim] = useState<AimPoint>("hull");
  const [firing, setFiring] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recentEvents, setRecentEvents] = useState<EventLogEntry[]>([]);

  // Get all ships
  const ships = Object.values(game.ships);

  // Get selected ship
  const selectedShip = selectedShipId ? game.ships[selectedShipId] : null;

  // Reset selections when ship changes
  useEffect(() => {
    setSelectedBroadside(null);
    setSelectedTarget(null);
    setError(null);
    onClearArc();
  }, [selectedShipId, onClearArc]);

  // Update arc visualization when broadside is selected
  useEffect(() => {
    if (selectedShip && selectedBroadside) {
      onBroadsideSelected(selectedShip.id, selectedBroadside);
    } else {
      onClearArc();
    }
  }, [selectedShip, selectedBroadside, onBroadsideSelected, onClearArc]);

  // Get potential targets when broadside is selected
  const potentialTargets = selectedShip && selectedBroadside
    ? getPotentialTargets(selectedShip, ships)
    : [];

  // Determine which ships can fire
  const shipsAbleToFire = ships.filter(canShipFire);

  const handleFire = async () => {
    if (!selectedShip || !selectedBroadside || !selectedTarget) {
      setError("Please select a ship, broadside, and target");
      return;
    }

    setFiring(true);
    setError(null);

    try {
      const response = await api.fireBroadside(game.id, game.turn_number, {
        ship_id: selectedShip.id,
        broadside: selectedBroadside,
        target_ship_id: selectedTarget,
        aim: selectedAim,
      });

      // Update game state
      onGameUpdate(response.state);

      // Store recent events for display
      setRecentEvents((prev) => [...prev, ...response.events]);

      // Reset selections after successful fire
      setSelectedBroadside(null);
      setSelectedTarget(null);
      setSelectedAim("hull");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fire broadside");
      console.error("Failed to fire broadside:", err);
    } finally {
      setFiring(false);
    }
  };

  // Only show in combat phase
  if (game.phase !== "combat") {
    return (
      <div
        style={{
          backgroundColor: "#1e1e1e",
          border: "2px solid #333",
          borderRadius: "8px",
          padding: "16px",
          color: "#e0e0e0",
        }}
      >
        <h3
          style={{
            margin: "0 0 12px 0",
            fontSize: "14px",
            fontWeight: "bold",
            color: "#aaa",
          }}
        >
          COMBAT
        </h3>
        <p style={{ fontSize: "13px", color: "#888", fontStyle: "italic" }}>
          Combat can only be conducted during the Combat phase
        </p>
      </div>
    );
  }

  return (
    <div
      style={{
        backgroundColor: "#1e1e1e",
        border: "2px solid #333",
        borderRadius: "8px",
        padding: "16px",
        color: "#e0e0e0",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
        height: "100%",
        overflow: "auto",
      }}
    >
      {/* Header */}
      <div>
        <h3
          style={{
            margin: "0 0 8px 0",
            fontSize: "14px",
            fontWeight: "bold",
            color: "#aaa",
          }}
        >
          BROADSIDE FIRE
        </h3>
        <p style={{ fontSize: "12px", color: "#888", marginBottom: "8px" }}>
          Select a ship from the board to fire
        </p>
      </div>

      {/* Ship selection list */}
      {!selectedShip && (
        <div style={{ flex: 1, overflow: "auto" }}>
          <div style={{ fontSize: "13px", color: "#aaa", marginBottom: "8px", fontWeight: "bold" }}>
            Ships Ready to Fire:
          </div>
          {shipsAbleToFire.length === 0 ? (
            <p style={{ fontSize: "13px", color: "#888", fontStyle: "italic" }}>
              No ships have loaded broadsides
            </p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {shipsAbleToFire.map((ship) => (
                <button
                  key={ship.id}
                  onClick={() => onShipSelect(ship.id)}
                  style={{
                    padding: "12px",
                    backgroundColor: "#2a2a2a",
                    border: "1px solid #444",
                    borderRadius: "6px",
                    color: "#fff",
                    textAlign: "left",
                    cursor: "pointer",
                    fontSize: "13px",
                  }}
                >
                  <div style={{ fontWeight: "bold", color: ship.side === "P1" ? "#4a90e2" : "#e24a4a" }}>
                    {ship.name}
                  </div>
                  <div style={{ fontSize: "11px", color: "#888", marginTop: "4px" }}>
                    L: {isBroadsideLoaded(ship, "L") ? "Loaded" : "Empty"} |
                    R: {isBroadsideLoaded(ship, "R") ? "Loaded" : "Empty"}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Selected ship firing controls */}
      {selectedShip && (
        <>
          {/* Selected ship info */}
          <div
            style={{
              backgroundColor: "#2a2a2a",
              border: "2px solid #444",
              borderRadius: "6px",
              padding: "12px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span
                style={{
                  fontSize: "14px",
                  fontWeight: "bold",
                  color: selectedShip.side === "P1" ? "#4a90e2" : "#e24a4a",
                }}
              >
                {selectedShip.name}
              </span>
              <button
                onClick={() => onShipSelect("")}
                style={{
                  padding: "4px 8px",
                  backgroundColor: "#1a1a1a",
                  border: "1px solid #555",
                  borderRadius: "4px",
                  color: "#888",
                  cursor: "pointer",
                  fontSize: "11px",
                }}
              >
                Change Ship
              </button>
            </div>
          </div>

          {/* Broadside selection */}
          <div>
            <div style={{ fontSize: "13px", color: "#aaa", marginBottom: "8px", fontWeight: "bold" }}>
              Select Broadside:
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
              <button
                onClick={() => setSelectedBroadside("L")}
                disabled={!isBroadsideLoaded(selectedShip, "L")}
                style={{
                  flex: 1,
                  padding: "10px",
                  backgroundColor: selectedBroadside === "L" ? "#4a90e2" : "#2a2a2a",
                  border: selectedBroadside === "L" ? "2px solid #4a90e2" : "1px solid #444",
                  borderRadius: "6px",
                  color: isBroadsideLoaded(selectedShip, "L") ? "#fff" : "#666",
                  cursor: isBroadsideLoaded(selectedShip, "L") ? "pointer" : "not-allowed",
                  fontSize: "12px",
                  fontWeight: "bold",
                }}
              >
                <div>PORT (L)</div>
                <div style={{ fontSize: "10px", marginTop: "4px" }}>
                  {selectedShip.guns_L} guns
                </div>
                <div style={{ fontSize: "10px" }}>
                  {isBroadsideLoaded(selectedShip, "L") ? "Loaded" : "Empty"}
                </div>
              </button>
              <button
                onClick={() => setSelectedBroadside("R")}
                disabled={!isBroadsideLoaded(selectedShip, "R")}
                style={{
                  flex: 1,
                  padding: "10px",
                  backgroundColor: selectedBroadside === "R" ? "#4a90e2" : "#2a2a2a",
                  border: selectedBroadside === "R" ? "2px solid #4a90e2" : "1px solid #444",
                  borderRadius: "6px",
                  color: isBroadsideLoaded(selectedShip, "R") ? "#fff" : "#666",
                  cursor: isBroadsideLoaded(selectedShip, "R") ? "pointer" : "not-allowed",
                  fontSize: "12px",
                  fontWeight: "bold",
                }}
              >
                <div>STARBOARD (R)</div>
                <div style={{ fontSize: "10px", marginTop: "4px" }}>
                  {selectedShip.guns_R} guns
                </div>
                <div style={{ fontSize: "10px" }}>
                  {isBroadsideLoaded(selectedShip, "R") ? "Loaded" : "Empty"}
                </div>
              </button>
            </div>
          </div>

          {/* Target selection */}
          {selectedBroadside && (
            <div style={{ flex: 1, overflow: "auto", minHeight: 0 }}>
              <div style={{ fontSize: "13px", color: "#aaa", marginBottom: "8px", fontWeight: "bold" }}>
                Select Target:
              </div>
              {potentialTargets.length === 0 ? (
                <p style={{ fontSize: "13px", color: "#888", fontStyle: "italic" }}>
                  No valid targets in arc
                </p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  {potentialTargets.map((targetInfo) => {
                    const isClosest = targetInfo.isClosest;
                    const target = targetInfo.ship;

                    return (
                      <button
                        key={target.id}
                        onClick={() => setSelectedTarget(target.id)}
                        disabled={!isClosest}
                        style={{
                          padding: "10px",
                          backgroundColor: selectedTarget === target.id ? "#4a90e2" : "#2a2a2a",
                          border: selectedTarget === target.id ? "2px solid #4a90e2" : "1px solid #444",
                          borderRadius: "6px",
                          color: isClosest ? "#fff" : "#666",
                          cursor: isClosest ? "pointer" : "not-allowed",
                          textAlign: "left",
                          fontSize: "12px",
                          opacity: isClosest ? 1 : 0.5,
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontWeight: "bold" }}>{target.name}</span>
                          <span style={{ fontSize: "11px", color: isClosest ? "#4ade80" : "#888" }}>
                            {targetInfo.distance} hexes {isClosest && "✓"}
                          </span>
                        </div>
                        <div style={{ fontSize: "11px", color: "#888", marginTop: "4px" }}>
                          Hull: {target.hull} | Rigging: {target.rigging}
                        </div>
                        {!isClosest && (
                          <div style={{ fontSize: "10px", color: "#e24a4a", marginTop: "4px", fontStyle: "italic" }}>
                            Not closest target (closest-target rule)
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Aim point selection */}
          {selectedBroadside && selectedTarget && (
            <div>
              <div style={{ fontSize: "13px", color: "#aaa", marginBottom: "8px", fontWeight: "bold" }}>
                Aim Point:
              </div>
              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  onClick={() => setSelectedAim("hull")}
                  style={{
                    flex: 1,
                    padding: "8px",
                    backgroundColor: selectedAim === "hull" ? "#4a90e2" : "#2a2a2a",
                    border: selectedAim === "hull" ? "2px solid #4a90e2" : "1px solid #444",
                    borderRadius: "6px",
                    color: "#fff",
                    cursor: "pointer",
                    fontSize: "12px",
                    fontWeight: "bold",
                  }}
                >
                  HULL
                </button>
                <button
                  onClick={() => setSelectedAim("rigging")}
                  style={{
                    flex: 1,
                    padding: "8px",
                    backgroundColor: selectedAim === "rigging" ? "#4a90e2" : "#2a2a2a",
                    border: selectedAim === "rigging" ? "2px solid #4a90e2" : "1px solid #444",
                    borderRadius: "6px",
                    color: "#fff",
                    cursor: "pointer",
                    fontSize: "12px",
                    fontWeight: "bold",
                  }}
                >
                  RIGGING
                </button>
              </div>
            </div>
          )}

          {/* Error message */}
          {error && (
            <div
              style={{
                padding: "8px",
                backgroundColor: "#e24a4a22",
                border: "1px solid #e24a4a",
                borderRadius: "4px",
                fontSize: "12px",
                color: "#e24a4a",
              }}
            >
              {error}
            </div>
          )}

          {/* Fire button */}
          {selectedBroadside && selectedTarget && (
            <button
              onClick={handleFire}
              disabled={firing}
              style={{
                padding: "12px 16px",
                backgroundColor: firing ? "#2a2a2a" : "#e24a4a",
                border: "none",
                borderRadius: "6px",
                color: firing ? "#666" : "#fff",
                cursor: firing ? "not-allowed" : "pointer",
                fontSize: "14px",
                fontWeight: "bold",
              }}
            >
              {firing ? "FIRING..." : "🔥 FIRE BROADSIDE"}
            </button>
          )}

          {/* Recent events display */}
          {recentEvents.length > 0 && (
            <div
              style={{
                maxHeight: "200px",
                overflow: "auto",
                backgroundColor: "#1a1a1a",
                border: "1px solid #444",
                borderRadius: "6px",
                padding: "12px",
              }}
            >
              <div style={{ fontSize: "13px", color: "#aaa", marginBottom: "8px", fontWeight: "bold" }}>
                Recent Combat Events:
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {recentEvents.slice().reverse().slice(0, 5).map((event, idx) => (
                  <div
                    key={`${event.turn_number}-${event.event_type}-${idx}`}
                    style={{
                      fontSize: "11px",
                      padding: "8px",
                      backgroundColor: "#2a2a2a",
                      borderRadius: "4px",
                      borderLeft: "3px solid #e24a4a",
                    }}
                  >
                    <div style={{ fontWeight: "bold", color: "#fff", marginBottom: "4px" }}>
                      {event.summary}
                    </div>
                    {event.dice_roll && (
                      <div style={{ color: "#888" }}>
                        Dice: [{event.dice_roll.rolls.join(", ")}] = {event.dice_roll.total}
                      </div>
                    )}
                    {event.modifiers && Object.keys(event.modifiers).length > 0 && (
                      <div style={{ color: "#888" }}>
                        Modifiers: {JSON.stringify(event.modifiers)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
