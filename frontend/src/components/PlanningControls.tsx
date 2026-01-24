// Planning phase controls for ship action panel
// Movement input with real-time validation and ready state management

import { useState, useEffect } from "react";
import type { Game, Ship, ShipOrders } from "../types/game";
import { api } from "../api/client";

interface PlanningControlsProps {
  ship: Ship;
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

export function PlanningControls({ ship, game, onGameUpdate, onPreviewPath }: PlanningControlsProps) {
  const [movement, setMovement] = useState<string>("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [markingReady, setMarkingReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isValid, setIsValid] = useState(false);

  // Get player's order status
  const playerOrdersData = ship.side === "P1" ? game.p1_orders : game.p2_orders;
  const hasSubmittedOrders = playerOrdersData !== null && playerOrdersData.orders.some(o => o.ship_id === ship.id);
  const isReady = playerOrdersData?.ready || false;

  // Check if ALL ships on this side have submitted orders
  const allShipsHaveOrders = (() => {
    const playerShips = Object.values(game.ships).filter(
      s => s.side === ship.side && !s.struck
    );

    if (!playerOrdersData || playerOrdersData.orders.length === 0) {
      return false;
    }

    // Check that every active ship has an order
    return playerShips.every(s =>
      playerOrdersData.orders.some(o => o.ship_id === s.id)
    );
  })();

  // Initialize movement from existing orders
  useEffect(() => {
    if (playerOrdersData && playerOrdersData.orders.length > 0) {
      const shipOrder = playerOrdersData.orders.find(o => o.ship_id === ship.id);
      if (shipOrder) {
        setMovement(shipOrder.movement_string);
        const validation = validateMovementSyntax(shipOrder.movement_string);
        setIsValid(validation.valid);
      }
    }
  }, [playerOrdersData, ship.id]);

  const handleMovementChange = (value: string) => {
    setMovement(value);

    // Validate and update state
    if (value.trim() === "") {
      setValidationError(null);
      setIsValid(false);
      if (onPreviewPath) {
        onPreviewPath(null, "");
      }
    } else {
      const validation = validateMovementSyntax(value);
      setIsValid(validation.valid);
      if (!validation.valid && validation.error) {
        setValidationError(validation.error);
      } else {
        setValidationError(null);
      }

      // Update preview
      if (onPreviewPath && validation.valid) {
        onPreviewPath(ship.id, value);
      }
    }
  };

  const handleSubmitOrders = async () => {
    if (!isValid || isReady) return;

    setSubmitting(true);
    setError(null);

    try {
      // Get all ships for this player
      const playerShips = Object.values(game.ships).filter(
        s => s.side === ship.side && !s.struck
      );

      // Build orders array - include this ship's order and any existing orders for other ships
      const ordersArray: ShipOrders[] = playerShips.map(s => {
        if (s.id === ship.id) {
          return {
            ship_id: ship.id,
            movement_string: movement.trim(),
          };
        } else {
          // Keep existing orders for other ships
          const existingOrder = playerOrdersData?.orders.find(o => o.ship_id === s.id);
          return {
            ship_id: s.id,
            movement_string: existingOrder?.movement_string || "0",
          };
        }
      });

      const response = await api.submitOrders(game.id, game.turn_number, {
        side: ship.side,
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
    if (!hasSubmittedOrders || isReady) return;

    setMarkingReady(true);
    setError(null);

    try {
      const response = await api.markReady(game.id, game.turn_number, {
        side: ship.side,
      });

      onGameUpdate(response.state);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to mark ready");
      console.error("Failed to mark ready:", err);
    } finally {
      setMarkingReady(false);
    }
  };

  const canSubmit = isValid && !isReady && !submitting;
  const canMarkReady = hasSubmittedOrders && allShipsHaveOrders && !isReady && !markingReady;

  return (
    <section
      aria-labelledby="planning-heading"
      className="movement-section"
      style={{
        marginTop: "24px",
        padding: "20px",
        background: "rgba(255, 255, 255, 0.4)",
        border: "2px dashed #8b7355",
        borderRadius: "8px",
      }}
    >
      <h3
        id="planning-heading"
        style={{
          margin: "0 0 16px 0",
          fontSize: "14px",
          fontWeight: 600,
          color: "#5a4a3a",
          textTransform: "uppercase",
          letterSpacing: "0.5px",
          fontFamily: "'Cinzel', serif",
        }}
      >
        Movement Orders
      </h3>

      {/* Ship speed info */}
      <div
        style={{
          fontSize: "12px",
          color: "#5a4a3a",
          marginBottom: "12px",
          display: "flex",
          justifyContent: "space-between",
        }}
      >
        <span>Battle Sail Speed:</span>
        <span style={{ fontWeight: 700 }}>{ship.battle_sail_speed}</span>
      </div>

      {/* Movement input */}
      <input
        type="text"
        value={movement}
        onChange={(e) => handleMovementChange(e.target.value)}
        onFocus={() => onPreviewPath && onPreviewPath(ship.id, movement)}
        onBlur={() => onPreviewPath && onPreviewPath(null, "")}
        disabled={isReady}
        placeholder="e.g., L1R1, 0, LLR2"
        aria-label="Movement orders input"
        aria-describedby="movement-help movement-validation"
        aria-invalid={!!validationError}
        className={`movement-input ${isValid && movement ? "valid" : validationError ? "invalid" : ""}`}
        style={{
          width: "100%",
          padding: "12px",
          fontFamily: "'Courier Prime', monospace",
          fontSize: "18px",
          textAlign: "center",
          letterSpacing: "2px",
          textTransform: "uppercase",
          background: isReady ? "#e8ddc8" : "white",
          border: `2px solid ${isValid && movement ? "#5a9a5a" : validationError ? "#a74a4a" : "#8b7355"}`,
          borderRadius: "4px",
          color: "#2c1810",
          transition: "border-color 0.2s",
          outline: "none",
          boxSizing: "border-box",
        }}
      />

      {/* Validation feedback */}
      {isValid && movement && (
        <div
          style={{
            marginTop: "8px",
            fontSize: "12px",
            color: "#4a8f4a",
            display: "flex",
            alignItems: "center",
            gap: "4px",
          }}
        >
          <span>✓</span>
          <span>Valid movement notation</span>
        </div>
      )}

      {validationError && (
        <div
          id="movement-validation"
          role="alert"
          aria-live="assertive"
          style={{
            marginTop: "8px",
            fontSize: "12px",
            color: "#a74a4a",
            animation: "shake 0.3s",
          }}
        >
          {validationError}
        </div>
      )}

      {/* Help text */}
      <div
        id="movement-help"
        style={{
          marginTop: "12px",
          fontSize: "11px",
          color: "#8b7d6b",
          backgroundColor: "rgba(255, 255, 255, 0.5)",
          padding: "8px",
          borderRadius: "4px",
        }}
      >
        <div style={{ fontWeight: "bold", marginBottom: "4px" }}>Syntax:</div>
        <div>• 0 = No movement</div>
        <div>• L = Turn left, R = Turn right</div>
        <div>• 1-9 = Move forward (hexes)</div>
      </div>

      {/* Error message */}
      {error && (
        <div
          style={{
            marginTop: "12px",
            padding: "8px",
            backgroundColor: "rgba(167, 74, 74, 0.1)",
            border: "1px solid #a74a4a",
            borderRadius: "4px",
            fontSize: "12px",
            color: "#a74a4a",
          }}
        >
          {error}
        </div>
      )}

      {/* Action buttons */}
      <div style={{ marginTop: "16px", display: "flex", flexDirection: "column", gap: "8px" }}>
        <button
          className="submit-button"
          onClick={handleSubmitOrders}
          disabled={!canSubmit}
          aria-label={hasSubmittedOrders ? "Update movement orders" : "Submit movement orders"}
          style={{
            width: "100%",
            padding: "14px",
            fontFamily: "'Cinzel', serif",
            fontSize: "14px",
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "1px",
            background: canSubmit ? "#4a7ba7" : "#d4c5a9",
            color: canSubmit ? "white" : "#8b7d6b",
            border: `2px solid ${canSubmit ? "#2c1810" : "#8b7355"}`,
            borderRadius: "4px",
            cursor: canSubmit ? "pointer" : "not-allowed",
            transition: "all 0.2s",
            opacity: canSubmit ? 1 : 0.5,
          }}
          onMouseEnter={(e) => {
            if (canSubmit) {
              e.currentTarget.style.background = "#5a8bc7";
              e.currentTarget.style.transform = "translateY(-1px)";
              e.currentTarget.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.2)";
            }
          }}
          onMouseLeave={(e) => {
            if (canSubmit) {
              e.currentTarget.style.background = "#4a7ba7";
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.boxShadow = "none";
            }
          }}
        >
          {submitting ? "Submitting..." : hasSubmittedOrders ? "Update Orders" : "Submit Orders"}
        </button>

        <button
          className="ready-button"
          onClick={handleMarkReady}
          disabled={!canMarkReady}
          aria-label={isReady ? "Orders marked as ready" : "Mark orders as ready"}
          aria-pressed={isReady}
          style={{
            width: "100%",
            padding: "14px",
            fontFamily: "'Cinzel', serif",
            fontSize: "14px",
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "1px",
            background: isReady ? "#d4c5a9" : canMarkReady ? "#4a8f4a" : "#d4c5a9",
            color: isReady ? "#4a8f4a" : canMarkReady ? "white" : "#8b7d6b",
            border: `2px solid ${isReady ? "#4a8f4a" : canMarkReady ? "#2c1810" : "#8b7355"}`,
            borderRadius: "4px",
            cursor: isReady ? "default" : canMarkReady ? "pointer" : "not-allowed",
            transition: "all 0.2s",
            opacity: canMarkReady || isReady ? 1 : 0.5,
          }}
          onMouseEnter={(e) => {
            if (canMarkReady) {
              e.currentTarget.style.background = "#5a9f5a";
              e.currentTarget.style.transform = "translateY(-1px)";
              e.currentTarget.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.2)";
            }
          }}
          onMouseLeave={(e) => {
            if (canMarkReady) {
              e.currentTarget.style.background = "#4a8f4a";
              e.currentTarget.style.transform = "translateY(0)";
              e.currentTarget.style.boxShadow = "none";
            }
          }}
        >
          {markingReady ? "Marking Ready..." : isReady ? "✓ Ready" : "Mark Ready"}
        </button>

        {/* Info message when not all ships have orders */}
        {hasSubmittedOrders && !allShipsHaveOrders && !isReady && (
          <div
            style={{
              marginTop: "8px",
              fontSize: "11px",
              color: "#8b7d6b",
              backgroundColor: "rgba(255, 255, 255, 0.5)",
              padding: "8px",
              borderRadius: "4px",
              border: "1px dashed #8b7355",
            }}
          >
            ℹ️ All ships must submit orders before marking ready
          </div>
        )}
      </div>

      {/* Add shake animation */}
      <style>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-4px); }
          75% { transform: translateX(4px); }
        }
      `}</style>
    </section>
  );
}
