// Orders panel for the planning phase
// Allows players to enter movement orders for their ships and mark ready

import { useState, useEffect } from "react";
import type { Game, Side, ShipOrders } from "../types/game";
import { api } from "../api/client";

interface OrdersPanelProps {
  game: Game;
  onGameUpdate: (game: Game) => void;
  onPreviewPath?: (shipId: string | null, movement: string) => void;
}

// Movement validation based on backend parser
// Valid: '0' (no movement), 'L'/'R' (turns), digits 1-9 (forward movement)
// Examples: 'L1R1', '0', 'LLR2', '3'
function validateMovementSyntax(movement: string): { valid: boolean; error?: string } {
  if (!movement || movement.trim() === "") {
    return { valid: false, error: "Movement cannot be empty" };
  }

  const normalized = movement.trim().toUpperCase();

  // Special case: '0' means no movement
  if (normalized === "0") {
    return { valid: true };
  }

  // Check each character is valid (L, R, or digit 1-9)
  for (let i = 0; i < normalized.length; i++) {
    const char = normalized[i];
    if (char !== "L" && char !== "R" && !/[1-9]/.test(char)) {
      return { valid: false, error: `Invalid character '${char}' at position ${i + 1}` };
    }
  }

  return { valid: true };
}

export function OrdersPanel({ game, onGameUpdate, onPreviewPath }: OrdersPanelProps) {
  const [currentPlayer, setCurrentPlayer] = useState<Side>("P1");
  const [orders, setOrders] = useState<Record<string, string>>({});
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [markingReady, setMarkingReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [focusedShipId, setFocusedShipId] = useState<string | null>(null);

  // Initialize orders from game state if already submitted
  useEffect(() => {
    const playerOrders = currentPlayer === "P1" ? game.p1_orders : game.p2_orders;
    if (playerOrders && playerOrders.orders.length > 0) {
      const ordersMap: Record<string, string> = {};
      for (const order of playerOrders.orders) {
        ordersMap[order.ship_id] = order.movement;
      }
      setOrders(ordersMap);
    }
  }, [game, currentPlayer]);

  // Get ships for current player
  const playerShips = Object.values(game.ships).filter(
    (ship) => ship.side === currentPlayer && !ship.struck
  );

  // Get order status for current player
  const playerOrdersData = currentPlayer === "P1" ? game.p1_orders : game.p2_orders;
  const hasSubmittedOrders = playerOrdersData !== null && playerOrdersData.orders.length > 0;
  const isReady = playerOrdersData?.ready || false;

  // Get opponent order status
  const opponentSide = currentPlayer === "P1" ? "P2" : "P1";
  const opponentOrdersData = opponentSide === "P1" ? game.p1_orders : game.p2_orders;
  const opponentIsReady = opponentOrdersData?.ready || false;

  // Check if all required orders are entered
  const allOrdersEntered = playerShips.every((ship) => {
    const order = orders[ship.id];
    return order && order.trim() !== "";
  });

  // Check if all orders are valid
  const allOrdersValid = playerShips.every((ship) => {
    const order = orders[ship.id];
    if (!order || order.trim() === "") return false;
    return validateMovementSyntax(order).valid;
  });

  const canSubmit = allOrdersEntered && allOrdersValid && !isReady && !submitting;
  const canMarkReady = hasSubmittedOrders && !isReady && !markingReady;

  const handleOrderChange = (shipId: string, movement: string) => {
    // Update orders
    setOrders((prev) => ({ ...prev, [shipId]: movement }));

    // Validate and update errors
    if (movement.trim() === "") {
      setValidationErrors((prev) => {
        const next = { ...prev };
        delete next[shipId];
        return next;
      });
    } else {
      const validation = validateMovementSyntax(movement);
      if (!validation.valid && validation.error) {
        setValidationErrors((prev) => ({ ...prev, [shipId]: validation.error! }));
      } else {
        setValidationErrors((prev) => {
          const next = { ...prev };
          delete next[shipId];
          return next;
        });
      }
    }

    // Update path preview if this ship is focused
    if (focusedShipId === shipId && onPreviewPath) {
      onPreviewPath(shipId, movement);
    }
  };

  const handleFocus = (shipId: string) => {
    setFocusedShipId(shipId);
    if (onPreviewPath) {
      const movement = orders[shipId] || "";
      onPreviewPath(shipId, movement);
    }
  };

  const handleBlur = () => {
    setFocusedShipId(null);
    if (onPreviewPath) {
      onPreviewPath(null, "");
    }
  };

  const handleSubmitOrders = async () => {
    if (!canSubmit) return;

    setSubmitting(true);
    setError(null);

    try {
      // Build orders array
      const ordersArray: ShipOrders[] = playerShips.map((ship) => ({
        ship_id: ship.id,
        movement: orders[ship.id].trim(),
      }));

      // Submit orders to API
      const response = await api.submitOrders(game.id, game.turn_number, {
        side: currentPlayer,
        orders: ordersArray,
      });

      onGameUpdate(response.state);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit orders");
      console.error("Failed to submit orders:", err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleMarkReady = async () => {
    if (!canMarkReady) return;

    setMarkingReady(true);
    setError(null);

    try {
      const response = await api.markReady(game.id, game.turn_number, {
        side: currentPlayer,
      });

      onGameUpdate(response.state);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to mark ready");
      console.error("Failed to mark ready:", err);
    } finally {
      setMarkingReady(false);
    }
  };

  // Only show in planning phase
  if (game.phase !== "planning") {
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
          ORDERS
        </h3>
        <p style={{ fontSize: "13px", color: "#888", fontStyle: "italic" }}>
          Orders can only be entered during the Planning phase
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
          MOVEMENT ORDERS
        </h3>

        {/* Player selector */}
        <div style={{ display: "flex", gap: "8px", marginBottom: "8px" }}>
          <button
            onClick={() => setCurrentPlayer("P1")}
            style={{
              flex: 1,
              padding: "6px 12px",
              backgroundColor: currentPlayer === "P1" ? "#4a90e2" : "#2a2a2a",
              border: "1px solid #444",
              borderRadius: "4px",
              color: "#fff",
              cursor: "pointer",
              fontSize: "12px",
              fontWeight: "bold",
            }}
          >
            PLAYER 1 {currentPlayer !== "P1" && opponentIsReady && "✓"}
          </button>
          <button
            onClick={() => setCurrentPlayer("P2")}
            style={{
              flex: 1,
              padding: "6px 12px",
              backgroundColor: currentPlayer === "P2" ? "#e24a4a" : "#2a2a2a",
              border: "1px solid #444",
              borderRadius: "4px",
              color: "#fff",
              cursor: "pointer",
              fontSize: "12px",
              fontWeight: "bold",
            }}
          >
            PLAYER 2 {currentPlayer !== "P2" && opponentIsReady && "✓"}
          </button>
        </div>

        {/* Ready status */}
        <div
          style={{
            fontSize: "12px",
            color: isReady ? "#4ade80" : "#888",
            marginBottom: "4px",
          }}
        >
          {isReady ? "✓ You are ready" : "○ Not ready"}
        </div>
        {opponentIsReady && (
          <div style={{ fontSize: "12px", color: "#4ade80" }}>
            ✓ Opponent is ready
          </div>
        )}
      </div>

      {/* Ship orders list */}
      <div style={{ flex: 1, overflow: "auto" }}>
        {playerShips.length === 0 ? (
          <p style={{ fontSize: "13px", color: "#888", fontStyle: "italic" }}>
            No ships available for orders
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {playerShips.map((ship) => {
              const order = orders[ship.id] || "";
              const validationError = validationErrors[ship.id];

              return (
                <div
                  key={ship.id}
                  style={{
                    backgroundColor: "#2a2a2a",
                    border: "1px solid #444",
                    borderRadius: "6px",
                    padding: "12px",
                  }}
                >
                  {/* Ship name and speed */}
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: "6px",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "13px",
                        fontWeight: "bold",
                        color: ship.side === "P1" ? "#4a90e2" : "#e24a4a",
                      }}
                    >
                      {ship.name}
                    </span>
                    <span
                      style={{
                        fontSize: "11px",
                        color: "#888",
                      }}
                    >
                      Speed {ship.battle_sail_speed}
                    </span>
                  </div>

                  {/* Movement input */}
                  <input
                    type="text"
                    value={order}
                    onChange={(e) => handleOrderChange(ship.id, e.target.value)}
                    onFocus={() => handleFocus(ship.id)}
                    onBlur={handleBlur}
                    disabled={isReady}
                    placeholder="e.g., L1R1, 0, LLR2"
                    style={{
                      width: "100%",
                      padding: "6px 8px",
                      backgroundColor: isReady ? "#1a1a1a" : "#1e1e1e",
                      border: validationError ? "1px solid #e24a4a" : focusedShipId === ship.id ? "1px solid #4a90e2" : "1px solid #555",
                      borderRadius: "4px",
                      color: "#fff",
                      fontSize: "12px",
                      boxSizing: "border-box",
                    }}
                  />

                  {/* Validation error */}
                  {validationError && (
                    <div
                      style={{
                        marginTop: "4px",
                        fontSize: "11px",
                        color: "#e24a4a",
                      }}
                    >
                      {validationError}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Help text */}
      <div
        style={{
          fontSize: "11px",
          color: "#666",
          backgroundColor: "#2a2a2a",
          padding: "8px",
          borderRadius: "4px",
        }}
      >
        <div style={{ fontWeight: "bold", marginBottom: "4px" }}>Movement Syntax:</div>
        <div>• 0 = No movement</div>
        <div>• L = Turn left, R = Turn right</div>
        <div>• 1-9 = Move forward (hexes)</div>
        <div>• Examples: L1R1, LLR2, 3</div>
      </div>

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

      {/* Action buttons */}
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {!hasSubmittedOrders && (
          <button
            onClick={handleSubmitOrders}
            disabled={!canSubmit}
            style={{
              padding: "10px 16px",
              backgroundColor: canSubmit ? "#4a90e2" : "#2a2a2a",
              border: "none",
              borderRadius: "6px",
              color: canSubmit ? "#fff" : "#666",
              cursor: canSubmit ? "pointer" : "not-allowed",
              fontSize: "13px",
              fontWeight: "bold",
            }}
          >
            {submitting ? "Submitting..." : "Submit Orders"}
          </button>
        )}

        {hasSubmittedOrders && !isReady && (
          <button
            onClick={handleMarkReady}
            disabled={!canMarkReady}
            style={{
              padding: "10px 16px",
              backgroundColor: canMarkReady ? "#4ade80" : "#2a2a2a",
              border: "none",
              borderRadius: "6px",
              color: canMarkReady ? "#000" : "#666",
              cursor: canMarkReady ? "pointer" : "not-allowed",
              fontSize: "13px",
              fontWeight: "bold",
            }}
          >
            {markingReady ? "Marking Ready..." : "Mark Ready"}
          </button>
        )}

        {isReady && !opponentIsReady && (
          <div
            style={{
              padding: "10px 16px",
              backgroundColor: "#2a2a2a",
              border: "1px solid #444",
              borderRadius: "6px",
              color: "#888",
              fontSize: "13px",
              textAlign: "center",
            }}
          >
            Waiting for opponent...
          </div>
        )}

        {isReady && opponentIsReady && (
          <div
            style={{
              padding: "10px 16px",
              backgroundColor: "#4ade8022",
              border: "1px solid #4ade80",
              borderRadius: "6px",
              color: "#4ade80",
              fontSize: "13px",
              textAlign: "center",
              fontWeight: "bold",
            }}
          >
            Both players ready! Proceed to movement phase.
          </div>
        )}
      </div>
    </div>
  );
}
