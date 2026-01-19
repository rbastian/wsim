// Ship log panel component - displays detailed ship information
// Mimics the ship log sheet from the physical board game

import type { Ship } from "../types/game";

interface ShipLogPanelProps {
  ship: Ship | null;
}

export function ShipLogPanel({ ship }: ShipLogPanelProps) {
  if (!ship) {
    return (
      <div style={styles.container}>
        <div style={styles.emptyState}>
          <p style={styles.emptyText}>Select a ship to view its log</p>
        </div>
      </div>
    );
  }

  // Helper to format load state
  const formatLoadState = (loadState: string): string => {
    return loadState === "R" ? "Loaded (Roundshot)" : "Empty";
  };

  // Helper to get load state color
  const getLoadStateColor = (loadState: string): string => {
    return loadState === "R" ? "#4caf50" : "#999";
  };

  // Helper to get side color
  const getSideColor = (side: string): string => {
    return side === "P1" ? "#2196f3" : "#f44336";
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerTop}>
          <h2 style={styles.shipName}>{ship.name}</h2>
          <span
            style={{
              ...styles.sideBadge,
              backgroundColor: getSideColor(ship.side),
            }}
          >
            {ship.side}
          </span>
        </div>
        {(ship.struck || ship.fouled) && (
          <div style={styles.statusBadges}>
            {ship.struck && <span style={styles.struckBadge}>STRUCK</span>}
            {ship.fouled && <span style={styles.fouledBadge}>FOULED</span>}
          </div>
        )}
      </div>

      {/* Ship Stats Section */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>Ship Stats</h3>
        <div style={styles.statsGrid}>
          <div style={styles.statItem}>
            <span style={styles.statLabel}>Battle Sail Speed:</span>
            <span style={styles.statValue}>{ship.battle_sail_speed}</span>
          </div>
          <div style={styles.statItem}>
            <span style={styles.statLabel}>Facing:</span>
            <span style={styles.statValue}>{ship.facing}</span>
          </div>
          <div style={styles.statItem}>
            <span style={styles.statLabel}>Position (Bow):</span>
            <span style={styles.statValue}>
              [{ship.bow_hex.col}, {ship.bow_hex.row}]
            </span>
          </div>
          <div style={styles.statItem}>
            <span style={styles.statLabel}>Position (Stern):</span>
            <span style={styles.statValue}>
              [{ship.stern_hex.col}, {ship.stern_hex.row}]
            </span>
          </div>
        </div>
      </div>

      {/* Damage Tracks Section */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>Damage Tracks</h3>
        <div style={styles.tracksContainer}>
          <div style={styles.trackRow}>
            <span style={styles.trackLabel}>Hull:</span>
            <div style={styles.trackBar}>
              <div
                style={{
                  ...styles.trackFill,
                  width: `${(ship.hull / 15) * 100}%`, // Assume max 15 for visualization
                  backgroundColor: ship.hull > 6 ? "#4caf50" : ship.hull > 3 ? "#ff9800" : "#f44336",
                }}
              />
              <span style={styles.trackValue}>{ship.hull}</span>
            </div>
          </div>

          <div style={styles.trackRow}>
            <span style={styles.trackLabel}>Rigging:</span>
            <div style={styles.trackBar}>
              <div
                style={{
                  ...styles.trackFill,
                  width: `${(ship.rigging / 12) * 100}%`, // Assume max 12 for visualization
                  backgroundColor:
                    ship.rigging > 6 ? "#4caf50" : ship.rigging > 3 ? "#ff9800" : "#f44336",
                }}
              />
              <span style={styles.trackValue}>{ship.rigging}</span>
            </div>
          </div>

          <div style={styles.trackRow}>
            <span style={styles.trackLabel}>Crew:</span>
            <div style={styles.trackBar}>
              <div
                style={{
                  ...styles.trackFill,
                  width: `${(ship.crew / 12) * 100}%`, // Assume max 12 for visualization
                  backgroundColor:
                    ship.crew > 6 ? "#4caf50" : ship.crew > 3 ? "#ff9800" : "#f44336",
                }}
              />
              <span style={styles.trackValue}>{ship.crew}</span>
            </div>
          </div>

          <div style={styles.trackRow}>
            <span style={styles.trackLabel}>Marines:</span>
            <div style={styles.trackBar}>
              <div
                style={{
                  ...styles.trackFill,
                  width: `${(ship.marines / 4) * 100}%`, // Assume max 4 for visualization
                  backgroundColor:
                    ship.marines > 2 ? "#4caf50" : ship.marines > 0 ? "#ff9800" : "#f44336",
                }}
              />
              <span style={styles.trackValue}>{ship.marines}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Guns Section */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>Armament</h3>
        <div style={styles.gunsContainer}>
          <div style={styles.broadsideCard}>
            <div style={styles.broadsideHeader}>
              <span style={styles.broadsideTitle}>Port (L)</span>
              <span
                style={{
                  ...styles.loadBadge,
                  color: getLoadStateColor(ship.load_L),
                  borderColor: getLoadStateColor(ship.load_L),
                }}
              >
                {formatLoadState(ship.load_L)}
              </span>
            </div>
            <div style={styles.gunStats}>
              <div style={styles.gunItem}>
                <span style={styles.gunLabel}>Guns:</span>
                <span style={styles.gunValue}>{ship.guns_L}</span>
              </div>
              {ship.carronades_L > 0 && (
                <div style={styles.gunItem}>
                  <span style={styles.gunLabel}>Carronades:</span>
                  <span style={styles.gunValue}>{ship.carronades_L}</span>
                </div>
              )}
            </div>
          </div>

          <div style={styles.broadsideCard}>
            <div style={styles.broadsideHeader}>
              <span style={styles.broadsideTitle}>Starboard (R)</span>
              <span
                style={{
                  ...styles.loadBadge,
                  color: getLoadStateColor(ship.load_R),
                  borderColor: getLoadStateColor(ship.load_R),
                }}
              >
                {formatLoadState(ship.load_R)}
              </span>
            </div>
            <div style={styles.gunStats}>
              <div style={styles.gunItem}>
                <span style={styles.gunLabel}>Guns:</span>
                <span style={styles.gunValue}>{ship.guns_R}</span>
              </div>
              {ship.carronades_R > 0 && (
                <div style={styles.gunItem}>
                  <span style={styles.gunLabel}>Carronades:</span>
                  <span style={styles.gunValue}>{ship.carronades_R}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Drift Tracking */}
      {ship.turns_without_bow_advance > 0 && (
        <div style={styles.section}>
          <h3 style={styles.sectionTitle}>Drift Status</h3>
          <div style={styles.driftWarning}>
            <span style={styles.driftText}>
              Turns without bow advance: {ship.turns_without_bow_advance}
            </span>
            {ship.turns_without_bow_advance >= 2 && (
              <span style={styles.driftAlert}>⚠️ Will drift next turn!</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Styles
const styles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: "#1e1e1e",
    border: "2px solid #333",
    borderRadius: "8px",
    padding: "16px",
    color: "#e0e0e0",
    height: "100%",
    overflowY: "auto",
  },
  emptyState: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: "100%",
    minHeight: "200px",
  },
  emptyText: {
    color: "#888",
    fontSize: "14px",
    fontStyle: "italic",
  },
  header: {
    borderBottom: "2px solid #444",
    paddingBottom: "12px",
    marginBottom: "16px",
  },
  headerTop: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "8px",
  },
  shipName: {
    margin: 0,
    fontSize: "20px",
    fontWeight: "bold",
    color: "#fff",
  },
  sideBadge: {
    padding: "4px 12px",
    borderRadius: "4px",
    fontSize: "12px",
    fontWeight: "bold",
    color: "#fff",
  },
  statusBadges: {
    display: "flex",
    gap: "8px",
  },
  struckBadge: {
    padding: "4px 8px",
    backgroundColor: "#f44336",
    borderRadius: "4px",
    fontSize: "11px",
    fontWeight: "bold",
    color: "#fff",
  },
  fouledBadge: {
    padding: "4px 8px",
    backgroundColor: "#ff9800",
    borderRadius: "4px",
    fontSize: "11px",
    fontWeight: "bold",
    color: "#fff",
  },
  section: {
    marginBottom: "20px",
  },
  sectionTitle: {
    margin: "0 0 12px 0",
    fontSize: "14px",
    fontWeight: "bold",
    color: "#aaa",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "1fr",
    gap: "8px",
  },
  statItem: {
    display: "flex",
    justifyContent: "space-between",
    padding: "6px",
    backgroundColor: "#252525",
    borderRadius: "4px",
  },
  statLabel: {
    fontSize: "13px",
    color: "#aaa",
  },
  statValue: {
    fontSize: "13px",
    fontWeight: "bold",
    color: "#fff",
  },
  tracksContainer: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  trackRow: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  trackLabel: {
    minWidth: "70px",
    fontSize: "13px",
    color: "#aaa",
  },
  trackBar: {
    flex: 1,
    height: "24px",
    backgroundColor: "#252525",
    borderRadius: "4px",
    position: "relative",
    overflow: "hidden",
  },
  trackFill: {
    height: "100%",
    transition: "width 0.3s ease",
    borderRadius: "4px",
  },
  trackValue: {
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    fontSize: "12px",
    fontWeight: "bold",
    color: "#fff",
    textShadow: "0 0 3px rgba(0,0,0,0.8)",
  },
  gunsContainer: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  broadsideCard: {
    backgroundColor: "#252525",
    borderRadius: "6px",
    padding: "12px",
  },
  broadsideHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "8px",
  },
  broadsideTitle: {
    fontSize: "14px",
    fontWeight: "bold",
    color: "#fff",
  },
  loadBadge: {
    fontSize: "11px",
    fontWeight: "bold",
    padding: "2px 8px",
    border: "1px solid",
    borderRadius: "4px",
  },
  gunStats: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  gunItem: {
    display: "flex",
    justifyContent: "space-between",
  },
  gunLabel: {
    fontSize: "12px",
    color: "#aaa",
  },
  gunValue: {
    fontSize: "12px",
    fontWeight: "bold",
    color: "#fff",
  },
  driftWarning: {
    backgroundColor: "#3d2b00",
    border: "1px solid #ff9800",
    borderRadius: "4px",
    padding: "12px",
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  driftText: {
    fontSize: "13px",
    color: "#ffb74d",
  },
  driftAlert: {
    fontSize: "12px",
    fontWeight: "bold",
    color: "#ff9800",
  },
};
