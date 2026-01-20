// Event log component for displaying chronological game events

import { useEffect, useRef, useState } from "react";
import type { EventLogEntry, GamePhase } from "../types/game";

interface EventLogProps {
  events: EventLogEntry[];
  currentTurn: number;
}

type FilterOption = "all" | GamePhase;

export function EventLog({ events, currentTurn }: EventLogProps) {
  const [filter, setFilter] = useState<FilterOption>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const logEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest events
  useEffect(() => {
    if (logEndRef.current && containerRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [events.length]);

  // Filter events by phase
  const filteredEvents = events.filter((event) => {
    if (filter !== "all" && event.phase !== filter) {
      return false;
    }
    if (typeFilter !== "all" && event.event_type !== typeFilter) {
      return false;
    }
    return true;
  });

  // Get unique event types for type filter dropdown
  const eventTypes = Array.from(new Set(events.map((e) => e.event_type))).sort();

  // Group events by turn
  const eventsByTurn = filteredEvents.reduce(
    (acc, event) => {
      if (!acc[event.turn_number]) {
        acc[event.turn_number] = [];
      }
      acc[event.turn_number].push(event);
      return acc;
    },
    {} as Record<number, EventLogEntry[]>
  );

  const phaseColors: Record<GamePhase, string> = {
    planning: "#4a90e2",
    movement: "#50c878",
    combat: "#e74c3c",
    reload: "#f39c12",
  };

  const formatDiceRoll = (event: EventLogEntry): string | null => {
    if (!event.dice_roll) return null;
    const { num_dice, die_type, rolls, total } = event.dice_roll;
    const rollsStr = rolls.join(", ");
    return `${num_dice}d${die_type}: [${rollsStr}] = ${total}`;
  };

  const formatModifiers = (modifiers?: Record<string, number>): string | null => {
    if (!modifiers || Object.keys(modifiers).length === 0) return null;
    const modStrs = Object.entries(modifiers).map(([key, value]) => {
      const sign = value >= 0 ? "+" : "";
      return `${key}: ${sign}${value}`;
    });
    return modStrs.join(", ");
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        backgroundColor: "#1e1e1e",
        border: "2px solid #333",
        borderRadius: "8px",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "2px solid #333",
          backgroundColor: "#252525",
        }}
      >
        <h3
          style={{
            margin: "0 0 12px 0",
            fontSize: "14px",
            fontWeight: "bold",
            color: "#aaa",
            letterSpacing: "0.5px",
          }}
        >
          EVENT LOG
        </h3>

        {/* Filters */}
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {/* Phase filter */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as FilterOption)}
            style={{
              padding: "4px 8px",
              fontSize: "12px",
              backgroundColor: "#1a1a1a",
              color: "#e0e0e0",
              border: "1px solid #444",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            <option value="all">All Phases</option>
            <option value="planning">Planning</option>
            <option value="movement">Movement</option>
            <option value="combat">Combat</option>
            <option value="reload">Reload</option>
          </select>

          {/* Type filter */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            style={{
              padding: "4px 8px",
              fontSize: "12px",
              backgroundColor: "#1a1a1a",
              color: "#e0e0e0",
              border: "1px solid #444",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            <option value="all">All Types</option>
            {eventTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>

          {/* Event count badge */}
          <div
            style={{
              padding: "4px 8px",
              fontSize: "12px",
              backgroundColor: "#333",
              color: "#aaa",
              borderRadius: "4px",
              display: "flex",
              alignItems: "center",
            }}
          >
            {filteredEvents.length} events
          </div>
        </div>
      </div>

      {/* Events list */}
      <div
        ref={containerRef}
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "12px",
        }}
      >
        {Object.keys(eventsByTurn).length === 0 ? (
          <div
            style={{
              textAlign: "center",
              padding: "2rem",
              color: "#666",
              fontSize: "13px",
              fontStyle: "italic",
            }}
          >
            No events to display
          </div>
        ) : (
          Object.entries(eventsByTurn)
            .sort(([a], [b]) => Number(a) - Number(b))
            .map(([turn, turnEvents]) => (
              <div key={turn} style={{ marginBottom: "16px" }}>
                {/* Turn header */}
                <div
                  style={{
                    padding: "6px 10px",
                    backgroundColor: Number(turn) === currentTurn ? "#2a4a2a" : "#2a2a2a",
                    borderLeft: "3px solid #4a90e2",
                    marginBottom: "8px",
                    fontSize: "12px",
                    fontWeight: "bold",
                    color: Number(turn) === currentTurn ? "#50c878" : "#888",
                    letterSpacing: "0.5px",
                  }}
                >
                  TURN {turn}
                  {Number(turn) === currentTurn && (
                    <span style={{ marginLeft: "8px", color: "#50c878" }}>(CURRENT)</span>
                  )}
                </div>

                {/* Events for this turn */}
                {turnEvents.map((event, idx) => (
                  <div
                    key={`${turn}-${idx}`}
                    style={{
                      marginBottom: "8px",
                      padding: "10px",
                      backgroundColor: "#252525",
                      border: "1px solid #333",
                      borderRadius: "4px",
                      fontSize: "12px",
                    }}
                  >
                    {/* Phase badge and event type */}
                    <div style={{ display: "flex", gap: "8px", marginBottom: "6px" }}>
                      <span
                        style={{
                          padding: "2px 6px",
                          backgroundColor: phaseColors[event.phase] + "20",
                          color: phaseColors[event.phase],
                          borderRadius: "3px",
                          fontSize: "10px",
                          fontWeight: "bold",
                          textTransform: "uppercase",
                          letterSpacing: "0.5px",
                        }}
                      >
                        {event.phase}
                      </span>
                      <span
                        style={{
                          padding: "2px 6px",
                          backgroundColor: "#333",
                          color: "#aaa",
                          borderRadius: "3px",
                          fontSize: "10px",
                          fontWeight: "normal",
                        }}
                      >
                        {event.event_type}
                      </span>
                    </div>

                    {/* Summary */}
                    <div
                      style={{
                        color: "#e0e0e0",
                        marginBottom: event.dice_roll || event.modifiers ? "6px" : "0",
                        lineHeight: "1.5",
                      }}
                    >
                      {event.summary}
                    </div>

                    {/* Dice roll */}
                    {event.dice_roll && (
                      <div
                        style={{
                          color: "#4a90e2",
                          fontSize: "11px",
                          fontFamily: "monospace",
                          marginTop: "4px",
                        }}
                      >
                        🎲 {formatDiceRoll(event)}
                      </div>
                    )}

                    {/* Modifiers */}
                    {event.modifiers && Object.keys(event.modifiers).length > 0 && (
                      <div
                        style={{
                          color: "#f39c12",
                          fontSize: "11px",
                          fontFamily: "monospace",
                          marginTop: "4px",
                        }}
                      >
                        ⚙️ {formatModifiers(event.modifiers)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ))
        )}
        <div ref={logEndRef} />
      </div>
    </div>
  );
}
