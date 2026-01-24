// Combat controls component for the combat phase
// Provides broadside selector, target selector, aim point selector, and fire button
// Styled with combat red theme and period typography per UX_REDESIGN.md Phase 4, Bead 8

import { useState, useEffect } from "react";
import type { Ship, Game, Broadside, AimPoint, BroadsideArcResponse } from "../types/game";
import { api } from "../api/client";

interface CombatControlsProps {
  ship: Ship;
  game: Game;
  onGameUpdate: (game: Game) => void;
  onBroadsideSelected: (shipId: string, broadside: Broadside) => void;
  onClearArc: () => void;
  onTargetSelected?: (targetId: string | null) => void;
  arcData: BroadsideArcResponse | null;
}

// Helper to check if broadside is loaded
function isBroadsideLoaded(ship: Ship, broadside: Broadside): boolean {
  const loadState = broadside === "L" ? ship.load_L : ship.load_R;
  return loadState === "R"; // R = Roundshot (loaded)
}

// Calculate distance between two hex coordinates
function hexDistance(a: { col: number; row: number }, b: { col: number; row: number }): number {
  const axialA = { q: a.col - Math.floor(a.row / 2), r: a.row };
  const axialB = { q: b.col - Math.floor(b.row / 2), r: b.row };

  return (
    (Math.abs(axialA.q - axialB.q) +
      Math.abs(axialA.q + axialA.r - axialB.q - axialB.r) +
      Math.abs(axialA.r - axialB.r)) /
    2
  );
}

export function CombatControls({
  ship,
  game,
  onGameUpdate,
  onBroadsideSelected,
  onClearArc,
  onTargetSelected,
  arcData,
}: CombatControlsProps) {
  const [selectedBroadside, setSelectedBroadside] = useState<Broadside | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<string | null>(null);
  const [selectedAim, setSelectedAim] = useState<AimPoint>("hull");
  const [firing, setFiring] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset selections when ship changes
  useEffect(() => {
    setSelectedBroadside(null);
    setSelectedTarget(null);
    setSelectedAim("hull");
    setError(null);
    onClearArc();
  }, [ship.id, onClearArc]);

  // Update arc visualization when broadside is selected
  useEffect(() => {
    if (selectedBroadside) {
      onBroadsideSelected(ship.id, selectedBroadside);
    } else {
      onClearArc();
    }
  }, [ship.id, selectedBroadside, onBroadsideSelected, onClearArc]);

  // Notify parent of target selection changes
  useEffect(() => {
    if (onTargetSelected) {
      onTargetSelected(selectedTarget);
    }
  }, [selectedTarget, onTargetSelected]);

  const handleBroadsideSelect = (broadside: Broadside) => {
    if (!isBroadsideLoaded(ship, broadside)) return;
    setSelectedBroadside(broadside);
    setSelectedTarget(null); // Reset target when changing broadside
  };

  const handleFire = async () => {
    if (!selectedBroadside || !selectedTarget) {
      setError("Please select a broadside and target");
      return;
    }

    setFiring(true);
    setError(null);

    try {
      const response = await api.fireBroadside(game.id, game.turn_number, {
        ship_id: ship.id,
        broadside: selectedBroadside,
        target_ship_id: selectedTarget,
        aim: selectedAim,
      });

      // Update game state
      onGameUpdate(response.state);

      // Reset selections after successful fire
      setSelectedBroadside(null);
      setSelectedTarget(null);
      setSelectedAim("hull");
      onClearArc();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fire broadside");
      console.error("Failed to fire broadside:", err);
    } finally {
      setFiring(false);
    }
  };

  // Check if ship has any loaded broadsides
  const hasLoadedBroadsides =
    isBroadsideLoaded(ship, "L") || isBroadsideLoaded(ship, "R");

  if (!hasLoadedBroadsides) {
    return (
      <section style={{ marginTop: "24px" }}>
        <p
          style={{
            fontSize: "13px",
            color: "#5a4a3a",
            fontStyle: "italic",
            textAlign: "center",
            padding: "16px",
            backgroundColor: "rgba(255, 255, 255, 0.3)",
            border: "2px solid #8b7355",
            borderRadius: "6px",
          }}
        >
          No loaded broadsides available
        </p>
      </section>
    );
  }

  // Get target ships from arc data
  const targetShips =
    selectedBroadside && arcData
      ? arcData.ships_in_arc
          .filter((shipId) => game.ships[shipId])
          .map((shipId) => {
            const targetShip = game.ships[shipId];
            const isValid = arcData.valid_targets.includes(shipId);
            const distance = hexDistance(ship.bow_hex, targetShip.bow_hex);
            return { ship: targetShip, distance, isValid };
          })
          .sort((a, b) => a.distance - b.distance)
      : [];

  return (
    <section
      aria-labelledby="combat-heading"
      style={{
        marginTop: "24px",
        fontFamily: "'Cinzel', serif",
      }}
    >
      <h3
        id="combat-heading"
        style={{
          margin: "0 0 16px 0",
          fontSize: "14px",
          fontWeight: 600,
          color: "#5a4a3a",
          textTransform: "uppercase",
          letterSpacing: "0.5px",
        }}
      >
        Combat Actions
      </h3>

      {/* Broadside Selector */}
      <div
        role="radiogroup"
        aria-label="Select broadside"
        style={{ display: "flex", gap: "12px", marginBottom: "16px" }}
      >
        {/* Port (L) */}
        <button
          className="broadside-button"
          role="radio"
          aria-checked={selectedBroadside === "L"}
          aria-label={`Port broadside, ${ship.guns_L} guns, ${
            isBroadsideLoaded(ship, "L") ? "Loaded" : "Empty"
          }`}
          onClick={() => handleBroadsideSelect("L")}
          disabled={!isBroadsideLoaded(ship, "L")}
          style={{
            flex: 1,
            padding: "16px",
            fontFamily: "'Cinzel', serif",
            fontSize: "16px",
            fontWeight: 700,
            background:
              isBroadsideLoaded(ship, "L") && selectedBroadside === "L"
                ? "#a74a4a"
                : isBroadsideLoaded(ship, "L")
                  ? "#d4c5a9"
                  : "rgba(139, 125, 107, 0.3)",
            color:
              isBroadsideLoaded(ship, "L") && selectedBroadside === "L"
                ? "white"
                : isBroadsideLoaded(ship, "L")
                  ? "#2c1810"
                  : "#8b7d6b",
            border:
              selectedBroadside === "L"
                ? "2px solid #f4d03f"
                : "2px solid #8b7355",
            borderRadius: "6px",
            cursor: isBroadsideLoaded(ship, "L") ? "pointer" : "not-allowed",
            transition: "all 0.2s",
            position: "relative",
            opacity: isBroadsideLoaded(ship, "L") ? 1 : 0.4,
            transform:
              isBroadsideLoaded(ship, "L") && selectedBroadside === "L"
                ? "scale(1.05)"
                : "scale(1)",
            boxShadow:
              isBroadsideLoaded(ship, "L") && selectedBroadside === "L"
                ? "0 0 12px rgba(244, 208, 63, 0.5)"
                : "none",
          }}
          onMouseEnter={(e) => {
            if (isBroadsideLoaded(ship, "L") && selectedBroadside !== "L") {
              e.currentTarget.style.transform = "translateY(-2px)";
              e.currentTarget.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.2)";
            }
          }}
          onMouseLeave={(e) => {
            if (selectedBroadside !== "L") {
              e.currentTarget.style.transform = "scale(1)";
              e.currentTarget.style.boxShadow = "none";
            }
          }}
        >
          <div>PORT (L)</div>
          <div style={{ fontSize: "12px", marginTop: "4px", fontWeight: 400 }}>
            {ship.guns_L} guns
          </div>
          {/* Load badge */}
          {isBroadsideLoaded(ship, "L") && (
            <div
              style={{
                position: "absolute",
                top: "-8px",
                right: "-8px",
                width: "24px",
                height: "24px",
                borderRadius: "50%",
                background: "#4a8f4a",
                border: "2px solid #f2ebdc",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "10px",
                fontWeight: 700,
                color: "white",
              }}
            >
              ●
            </div>
          )}
        </button>

        {/* Starboard (R) */}
        <button
          className="broadside-button"
          role="radio"
          aria-checked={selectedBroadside === "R"}
          aria-label={`Starboard broadside, ${ship.guns_R} guns, ${
            isBroadsideLoaded(ship, "R") ? "Loaded" : "Empty"
          }`}
          onClick={() => handleBroadsideSelect("R")}
          disabled={!isBroadsideLoaded(ship, "R")}
          style={{
            flex: 1,
            padding: "16px",
            fontFamily: "'Cinzel', serif",
            fontSize: "16px",
            fontWeight: 700,
            background:
              isBroadsideLoaded(ship, "R") && selectedBroadside === "R"
                ? "#a74a4a"
                : isBroadsideLoaded(ship, "R")
                  ? "#d4c5a9"
                  : "rgba(139, 125, 107, 0.3)",
            color:
              isBroadsideLoaded(ship, "R") && selectedBroadside === "R"
                ? "white"
                : isBroadsideLoaded(ship, "R")
                  ? "#2c1810"
                  : "#8b7d6b",
            border:
              selectedBroadside === "R"
                ? "2px solid #f4d03f"
                : "2px solid #8b7355",
            borderRadius: "6px",
            cursor: isBroadsideLoaded(ship, "R") ? "pointer" : "not-allowed",
            transition: "all 0.2s",
            position: "relative",
            opacity: isBroadsideLoaded(ship, "R") ? 1 : 0.4,
            transform:
              isBroadsideLoaded(ship, "R") && selectedBroadside === "R"
                ? "scale(1.05)"
                : "scale(1)",
            boxShadow:
              isBroadsideLoaded(ship, "R") && selectedBroadside === "R"
                ? "0 0 12px rgba(244, 208, 63, 0.5)"
                : "none",
          }}
          onMouseEnter={(e) => {
            if (isBroadsideLoaded(ship, "R") && selectedBroadside !== "R") {
              e.currentTarget.style.transform = "translateY(-2px)";
              e.currentTarget.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.2)";
            }
          }}
          onMouseLeave={(e) => {
            if (selectedBroadside !== "R") {
              e.currentTarget.style.transform = "scale(1)";
              e.currentTarget.style.boxShadow = "none";
            }
          }}
        >
          <div>STARBOARD (R)</div>
          <div style={{ fontSize: "12px", marginTop: "4px", fontWeight: 400 }}>
            {ship.guns_R} guns
          </div>
          {/* Load badge */}
          {isBroadsideLoaded(ship, "R") && (
            <div
              style={{
                position: "absolute",
                top: "-8px",
                right: "-8px",
                width: "24px",
                height: "24px",
                borderRadius: "50%",
                background: "#4a8f4a",
                border: "2px solid #f2ebdc",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "10px",
                fontWeight: 700,
                color: "white",
              }}
            >
              ●
            </div>
          )}
        </button>
      </div>

      {/* Target Selector */}
      {selectedBroadside && (
        <div
          style={{
            marginTop: "20px",
            padding: "16px",
            background: "rgba(255, 255, 255, 0.3)",
            border: "2px solid #8b7355",
            borderRadius: "6px",
          }}
        >
          <h4
            style={{
              margin: "0 0 12px 0",
              fontSize: "13px",
              fontWeight: 600,
              color: "#2c1810",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
            }}
          >
            Select Target
          </h4>
          {targetShips.length === 0 ? (
            <p
              style={{
                fontSize: "13px",
                color: "#5a4a3a",
                fontStyle: "italic",
                margin: 0,
              }}
            >
              No valid targets in arc
            </p>
          ) : (
            <div
              style={{
                maxHeight: "200px",
                overflowY: "auto",
                display: "flex",
                flexDirection: "column",
                gap: "8px",
              }}
            >
              {targetShips.map(({ ship: targetShip, distance, isValid }) => (
                <button
                  className="target-item"
                  key={targetShip.id}
                  onClick={() => isValid && setSelectedTarget(targetShip.id)}
                  disabled={!isValid}
                  style={{
                    padding: "12px",
                    background:
                      selectedTarget === targetShip.id
                        ? "rgba(244, 208, 63, 0.1)"
                        : "white",
                    border:
                      selectedTarget === targetShip.id
                        ? "2px solid #f4d03f"
                        : "2px solid #8b7355",
                    borderRadius: "4px",
                    cursor: isValid ? "pointer" : "not-allowed",
                    textAlign: "left",
                    transition: "all 0.2s",
                    opacity: isValid ? 1 : 0.5,
                    boxShadow:
                      selectedTarget === targetShip.id
                        ? "0 0 8px rgba(244, 208, 63, 0.3)"
                        : "none",
                  }}
                  onMouseEnter={(e) => {
                    if (isValid && selectedTarget !== targetShip.id) {
                      e.currentTarget.style.borderColor = "#a74a4a";
                      e.currentTarget.style.transform = "translateX(4px)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (selectedTarget !== targetShip.id) {
                      e.currentTarget.style.borderColor = "#8b7355";
                      e.currentTarget.style.transform = "translateX(0)";
                    }
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: "4px",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "13px",
                        fontWeight: 600,
                        color: "#2c1810",
                      }}
                    >
                      {targetShip.name}
                    </span>
                    <span
                      style={{
                        fontSize: "11px",
                        fontWeight: 600,
                        color: isValid ? "#4a8f4a" : "#8b7d6b",
                      }}
                    >
                      {distance} hexes {isValid && "✓"}
                    </span>
                  </div>
                  <div
                    style={{
                      fontSize: "11px",
                      color: "#5a4a3a",
                    }}
                  >
                    Hull: {targetShip.hull} | Rigging: {targetShip.rigging}
                  </div>
                  {!isValid && (
                    <div
                      style={{
                        fontSize: "10px",
                        color: "#a74a4a",
                        marginTop: "4px",
                        fontStyle: "italic",
                      }}
                    >
                      Not closest target
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Aim Point Selector */}
      {selectedBroadside && selectedTarget && (
        <div style={{ marginTop: "16px" }}>
          <h4
            style={{
              margin: "0 0 8px 0",
              fontSize: "13px",
              fontWeight: 600,
              color: "#2c1810",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
            }}
          >
            Aim Point
          </h4>
          <div style={{ display: "flex", gap: "12px" }}>
            <button
              className="aim-button"
              onClick={() => setSelectedAim("hull")}
              style={{
                flex: 1,
                padding: "12px",
                fontFamily: "'Cinzel', serif",
                fontSize: "14px",
                fontWeight: 600,
                textTransform: "uppercase",
                background: selectedAim === "hull" ? "#a74a4a" : "white",
                color: selectedAim === "hull" ? "white" : "#2c1810",
                border:
                  selectedAim === "hull"
                    ? "2px solid #a74a4a"
                    : "2px solid #8b7355",
                borderRadius: "4px",
                cursor: "pointer",
                transition: "all 0.2s",
              }}
            >
              Hull
            </button>
            <button
              className="aim-button"
              onClick={() => setSelectedAim("rigging")}
              style={{
                flex: 1,
                padding: "12px",
                fontFamily: "'Cinzel', serif",
                fontSize: "14px",
                fontWeight: 600,
                textTransform: "uppercase",
                background: selectedAim === "rigging" ? "#a74a4a" : "white",
                color: selectedAim === "rigging" ? "white" : "#2c1810",
                border:
                  selectedAim === "rigging"
                    ? "2px solid #a74a4a"
                    : "2px solid #8b7355",
                borderRadius: "4px",
                cursor: "pointer",
                transition: "all 0.2s",
              }}
            >
              Rigging
            </button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div
          role="alert"
          style={{
            marginTop: "16px",
            padding: "12px",
            background: "rgba(167, 74, 74, 0.1)",
            border: "2px solid #a74a4a",
            borderRadius: "4px",
            fontSize: "12px",
            color: "#a74a4a",
            fontWeight: 600,
          }}
        >
          {error}
        </div>
      )}

      {/* Fire Button */}
      {selectedBroadside && selectedTarget && (
        <button
          onClick={handleFire}
          disabled={firing}
          className="fire-button"
          style={{
            width: "100%",
            padding: "18px",
            marginTop: "20px",
            fontFamily: "'IM Fell English', serif",
            fontSize: "18px",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "2px",
            background: firing ? "#8b7355" : "#a74a4a",
            color: "white",
            border: "3px solid #2c1810",
            borderRadius: "6px",
            cursor: firing ? "not-allowed" : "pointer",
            transition: "all 0.2s",
            position: "relative",
            overflow: "hidden",
            opacity: firing ? 0.5 : 1,
          }}
          onMouseEnter={(e) => {
            if (!firing) {
              e.currentTarget.style.transform = "scale(1.05)";
              e.currentTarget.style.boxShadow =
                "0 6px 20px rgba(167, 74, 74, 0.4)";
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "scale(1)";
            e.currentTarget.style.boxShadow = "none";
          }}
          onMouseDown={(e) => {
            if (!firing) {
              e.currentTarget.style.transform = "scale(0.98)";
            }
          }}
          onMouseUp={(e) => {
            if (!firing) {
              e.currentTarget.style.transform = "scale(1.05)";
            }
          }}
        >
          {firing ? "Firing..." : "🔥 Fire Broadside"}
        </button>
      )}

      {/* Add ripple effect animation for Fire Broadside button */}
      <style>{`
        .fire-broadside-button::before {
          content: '';
          position: absolute;
          top: 50%;
          left: 50%;
          width: 0;
          height: 0;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.3);
          transform: translate(-50%, -50%);
          transition: width 0.6s, height 0.6s;
        }

        .fire-broadside-button:hover:not(:disabled)::before {
          width: 300px;
          height: 300px;
        }
      `}</style>
    </section>
  );
}
