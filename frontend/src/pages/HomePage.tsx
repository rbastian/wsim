import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { ScenarioInfo } from "../types/game";

export function HomePage() {
  const navigate = useNavigate();
  const [scenarios, setScenarios] = useState<ScenarioInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState<string | null>(null);

  useEffect(() => {
    loadScenarios();
  }, []);

  async function loadScenarios() {
    try {
      setLoading(true);
      setError(null);
      const data = await api.listScenarios();
      setScenarios(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load scenarios");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateGame(scenarioId: string) {
    try {
      setCreating(scenarioId);
      setError(null);
      const response = await api.createGame({ scenario_id: scenarioId });
      navigate(`/game/${response.game_id}`);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`Failed to create game: ${err.message}`);
      } else {
        setError("Failed to create game");
      }
      setCreating(null);
    }
  }

  return (
    <div style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto" }}>
      <h1>Wooden Ships & Iron Men</h1>
      <p>Select a scenario to begin a new game.</p>

      {error && (
        <div
          style={{
            padding: "1rem",
            marginBottom: "1rem",
            backgroundColor: "#fee",
            border: "1px solid #fcc",
            borderRadius: "4px",
            color: "#c00",
          }}
        >
          {error}
        </div>
      )}

      {loading ? (
        <p>Loading scenarios...</p>
      ) : scenarios.length === 0 ? (
        <p>No scenarios available.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {scenarios.map((scenario) => (
            <div
              key={scenario.id}
              style={{
                border: "1px solid #ccc",
                borderRadius: "8px",
                padding: "1rem",
                backgroundColor: "#f9f9f9",
              }}
            >
              <h3 style={{ marginTop: 0 }}>{scenario.name}</h3>
              <p style={{ color: "#666" }}>{scenario.description}</p>
              <button
                onClick={() => handleCreateGame(scenario.id)}
                disabled={creating === scenario.id}
                style={{
                  padding: "0.5rem 1rem",
                  fontSize: "1rem",
                  backgroundColor: creating === scenario.id ? "#ccc" : "#007bff",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: creating === scenario.id ? "not-allowed" : "pointer",
                }}
              >
                {creating === scenario.id ? "Creating..." : "Start Game"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
