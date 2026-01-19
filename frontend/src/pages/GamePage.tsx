// Main game page with board, ship inspector, orders panel, etc.

import { useParams } from "react-router-dom";

export function GamePage() {
  const { gameId } = useParams<{ gameId: string }>();

  return (
    <div>
      <h1>Game: {gameId}</h1>
      <p>This is a placeholder for the game board and controls.</p>
    </div>
  );
}
