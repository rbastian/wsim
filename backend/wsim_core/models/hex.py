"""Hex coordinate models."""

from pydantic import BaseModel, Field


class HexCoord(BaseModel):
    """Hex coordinate (col, row)."""

    col: int = Field(ge=0, description="Column (x-axis)")
    row: int = Field(ge=0, description="Row (y-axis)")

    def __hash__(self) -> int:
        """Allow use as dict key."""
        return hash((self.col, self.row))

    def __eq__(self, other: object) -> bool:
        """Compare coordinates."""
        if not isinstance(other, HexCoord):
            return NotImplemented
        return self.col == other.col and self.row == other.row

    def __repr__(self) -> str:
        """String representation."""
        return f"HexCoord({self.col}, {self.row})"
