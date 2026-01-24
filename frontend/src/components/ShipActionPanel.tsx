// Ship action panel component - collapsible side panel for ship interactions
// Slides in from right when ship is selected, displays ship status and phase-specific controls

import { useEffect, useRef } from "react";
import type { Ship, Game } from "../types/game";

interface ShipActionPanelProps {
  id?: string;
  isOpen: boolean;
  selectedShip: Ship | null;
  game: Game;
  onClose: () => void;
  children?: React.ReactNode;
  isReady?: boolean;
}

export function ShipActionPanel({ id = "ship-action-panel", isOpen, selectedShip, game, onClose, children, isReady = false }: ShipActionPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  // Handle ESC key press
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  // Handle click outside panel
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (isOpen && panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    // Add a slight delay to prevent immediate closing when opening the panel
    const timeoutId = setTimeout(() => {
      document.addEventListener("mousedown", handleClickOutside);
    }, 100);

    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, onClose]);

  // Focus management
  useEffect(() => {
    if (isOpen && panelRef.current) {
      // Focus the panel when opened
      panelRef.current.focus();
    }
  }, [isOpen]);

  if (!selectedShip) {
    return null;
  }

  // Helper to get side color
  const getSideColor = (side: string): string => {
    return side === "P1" ? "#3a5ba7" : "#a73a3a";
  };

  return (
    <aside
      id={id}
      ref={panelRef}
      role="complementary"
      aria-label="Ship actions panel"
      aria-hidden={!isOpen}
      tabIndex={-1}
      className={`ship-action-panel ${isOpen ? 'open' : ''}`}
      style={{
        position: "fixed",
        right: 0,
        top: "80px",
        width: "380px",
        height: "calc(100vh - 80px)",
        background: "linear-gradient(180deg, #f2ebdc 0%, #e8ddc8 100%)",
        borderLeft: "3px solid #8b7355",
        boxShadow: "-4px 0 16px rgba(0, 0, 0, 0.3)",
        overflowY: "auto",
        padding: "24px",
        transform: isOpen ? "translateX(0)" : "translateX(100%)",
        transition: "transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        zIndex: 999,
        outline: "none",
        // Paper texture overlay
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='200' height='200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' /%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.05'/%3E%3C/svg%3E")`,
      }}
    >
      {/* Panel Header */}
      <header
        className="panel-header"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
          paddingBottom: "16px",
          borderBottom: "2px solid #8b7355",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <h2
            style={{
              margin: 0,
              fontFamily: "'IM Fell English', serif",
              fontSize: "22px",
              fontWeight: 700,
              color: "#2c1810",
            }}
          >
            {selectedShip.name}
          </h2>
          <span
            className="side-badge"
            style={{
              display: "inline-block",
              padding: "4px 12px",
              borderRadius: "4px",
              fontSize: "12px",
              fontWeight: 600,
              backgroundColor: getSideColor(selectedShip.side),
              color: "white",
            }}
          >
            {selectedShip.side}
          </span>
          {isReady && game.phase === 'planning' && (
            <span
              style={{
                display: "inline-block",
                padding: "4px 12px",
                borderRadius: "4px",
                fontSize: "12px",
                fontWeight: 600,
                backgroundColor: "#4a8f4a",
                color: "white",
                border: "2px solid #2c1810",
              }}
              title="Ship orders submitted and marked ready"
            >
              ✓ Ready
            </span>
          )}
        </div>
        <button
          onClick={onClose}
          aria-label="Close panel"
          aria-keyshortcuts="Escape"
          style={{
            background: "none",
            border: "none",
            fontSize: "28px",
            color: "#5a4a3a",
            cursor: "pointer",
            padding: 0,
            width: "32px",
            height: "32px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "color 0.2s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "#2c1810")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "#5a4a3a")}
        >
          ×
        </button>
      </header>

      {/* Status badges */}
      {(selectedShip.struck || selectedShip.fouled) && (
        <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
          {selectedShip.struck && (
            <span
              style={{
                padding: "4px 8px",
                backgroundColor: "#6a6a6a",
                borderRadius: "4px",
                fontSize: "11px",
                fontWeight: "bold",
                color: "#fff",
              }}
            >
              STRUCK
            </span>
          )}
          {selectedShip.fouled && (
            <span
              style={{
                padding: "4px 8px",
                backgroundColor: "#d4874f",
                borderRadius: "4px",
                fontSize: "11px",
                fontWeight: "bold",
                color: "#fff",
              }}
            >
              FOULED
            </span>
          )}
        </div>
      )}

      {/* Ship Status Section */}
      <section aria-labelledby="status-heading" style={{ marginBottom: "24px" }}>
        <h3
          id="status-heading"
          className="ship-status-heading"
          style={{
            margin: "0 0 12px 0",
            fontSize: "14px",
            fontWeight: 600,
            color: "#5a4a3a",
            textTransform: "uppercase",
            letterSpacing: "0.5px",
            fontFamily: "'Cinzel', serif",
          }}
        >
          Ship Status
        </h3>

        {/* Damage Tracks */}
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {/* Hull */}
          <div>
            <div
              className="damage-track-label"
              style={{
                fontSize: "12px",
                fontWeight: 600,
                color: "#5a4a3a",
                marginBottom: "4px",
                display: "flex",
                justifyContent: "space-between",
              }}
            >
              <span>Hull</span>
              <span>{selectedShip.hull}</span>
            </div>
            <div
              className="damage-track-bar"
              role="progressbar"
              aria-label="Hull integrity"
              aria-valuenow={selectedShip.hull}
              aria-valuemin={0}
              aria-valuemax={15}
              style={{
                width: "100%",
                height: "24px",
                backgroundColor: "rgba(139, 125, 107, 0.2)",
                border: "1px solid #8b7355",
                borderRadius: "4px",
                overflow: "hidden",
                position: "relative",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${(selectedShip.hull / 15) * 100}%`,
                  background: "linear-gradient(90deg, #a74a4a 0%, #d4874f 100%)",
                  transition: "width 0.4s ease-out",
                  filter: selectedShip.hull > 10 ? "hue-rotate(60deg) saturate(0.8)" : selectedShip.hull > 5 ? "saturate(1)" : "saturate(1.2) brightness(1.1)",
                  animation: selectedShip.hull < 5 ? "pulse-critical 1.5s ease-in-out infinite" : "none",
                }}
              />
            </div>
          </div>

          {/* Rigging */}
          <div>
            <div
              className="damage-track-label"
              style={{
                fontSize: "12px",
                fontWeight: 600,
                color: "#5a4a3a",
                marginBottom: "4px",
                display: "flex",
                justifyContent: "space-between",
              }}
            >
              <span>Rigging</span>
              <span>{selectedShip.rigging}</span>
            </div>
            <div
              className="damage-track-bar"
              role="progressbar"
              aria-label="Rigging integrity"
              aria-valuenow={selectedShip.rigging}
              aria-valuemin={0}
              aria-valuemax={12}
              style={{
                width: "100%",
                height: "24px",
                backgroundColor: "rgba(139, 125, 107, 0.2)",
                border: "1px solid #8b7355",
                borderRadius: "4px",
                overflow: "hidden",
                position: "relative",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${(selectedShip.rigging / 12) * 100}%`,
                  background: "linear-gradient(90deg, #8b7355 0%, #d4c5a9 100%)",
                  transition: "width 0.4s ease-out",
                  filter: selectedShip.rigging > 8 ? "hue-rotate(60deg) saturate(0.8)" : selectedShip.rigging > 4 ? "saturate(1)" : "saturate(1.2) brightness(1.1)",
                  animation: selectedShip.rigging < 4 ? "pulse-critical 1.5s ease-in-out infinite" : "none",
                }}
              />
            </div>
          </div>

          {/* Crew */}
          <div>
            <div
              className="damage-track-label"
              style={{
                fontSize: "12px",
                fontWeight: 600,
                color: "#5a4a3a",
                marginBottom: "4px",
                display: "flex",
                justifyContent: "space-between",
              }}
            >
              <span>Crew</span>
              <span>{selectedShip.crew}</span>
            </div>
            <div
              className="damage-track-bar"
              role="progressbar"
              aria-label="Crew complement"
              aria-valuenow={selectedShip.crew}
              aria-valuemin={0}
              aria-valuemax={12}
              style={{
                width: "100%",
                height: "24px",
                backgroundColor: "rgba(139, 125, 107, 0.2)",
                border: "1px solid #8b7355",
                borderRadius: "4px",
                overflow: "hidden",
                position: "relative",
              }}
            >
              <div
                style={{
                  height: "100%",
                  width: `${(selectedShip.crew / 12) * 100}%`,
                  background: "linear-gradient(90deg, #4a7ba7 0%, #7a9bc7 100%)",
                  transition: "width 0.4s ease-out",
                  filter: selectedShip.crew > 8 ? "hue-rotate(60deg) saturate(0.8)" : selectedShip.crew > 4 ? "saturate(1)" : "saturate(1.2) brightness(1.1)",
                  animation: selectedShip.crew < 4 ? "pulse-critical 1.5s ease-in-out infinite" : "none",
                }}
              />
            </div>
          </div>
        </div>

        {/* Load Status */}
        <div className="armament-section" style={{ marginTop: "16px" }}>
          <h4
            style={{
              margin: "0 0 8px 0",
              fontSize: "12px",
              fontWeight: 600,
              color: "#5a4a3a",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
            }}
          >
            Armament
          </h4>
          <div style={{ display: "flex", gap: "12px" }}>
            {/* Port (L) */}
            <div
              className="armament-box"
              style={{
                flex: 1,
                padding: "8px",
                backgroundColor: "rgba(255, 255, 255, 0.4)",
                border: "1px solid #8b7355",
                borderRadius: "4px",
              }}
            >
              <div style={{ fontSize: "11px", fontWeight: 600, color: "#2c1810", marginBottom: "4px" }}>
                Port (L)
              </div>
              <div style={{ fontSize: "10px", color: "#5a4a3a" }}>
                {selectedShip.guns_L} guns
              </div>
              <div
                style={{
                  fontSize: "10px",
                  fontWeight: "bold",
                  color: selectedShip.load_L === "R" ? "#4a8f4a" : "#6a6a6a",
                  marginTop: "4px",
                }}
              >
                {selectedShip.load_L === "R" ? "Loaded" : "Empty"}
              </div>
            </div>

            {/* Starboard (R) */}
            <div
              className="armament-box"
              style={{
                flex: 1,
                padding: "8px",
                backgroundColor: "rgba(255, 255, 255, 0.4)",
                border: "1px solid #8b7355",
                borderRadius: "4px",
              }}
            >
              <div style={{ fontSize: "11px", fontWeight: 600, color: "#2c1810", marginBottom: "4px" }}>
                Starboard (R)
              </div>
              <div style={{ fontSize: "10px", color: "#5a4a3a" }}>
                {selectedShip.guns_R} guns
              </div>
              <div
                style={{
                  fontSize: "10px",
                  fontWeight: "bold",
                  color: selectedShip.load_R === "R" ? "#4a8f4a" : "#6a6a6a",
                  marginTop: "4px",
                }}
              >
                {selectedShip.load_R === "R" ? "Loaded" : "Empty"}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Phase-specific content */}
      {children}

      {/* Add keyframe animation for critical damage pulse */}
      <style>{`
        @keyframes pulse-critical {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
      `}</style>
    </aside>
  );
}
