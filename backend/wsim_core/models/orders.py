"""Orders and planning phase models."""

from pydantic import BaseModel, Field


class ShipOrders(BaseModel):
    """Movement orders for a single ship for one turn."""

    ship_id: str = Field(description="Ship identifier")
    movement_string: str = Field(
        description="Movement notation (e.g., 'L1R1', '0', 'LLR2')",
        pattern=r"^[0-9LR]+$",  # Basic pattern validation: digits, L, R
    )


class TurnOrders(BaseModel):
    """All orders for one player for one turn."""

    turn_number: int = Field(ge=1, description="Turn number")
    side: str = Field(description="Player side (P1 or P2)")
    orders: list[ShipOrders] = Field(description="Orders for each ship")
    submitted: bool = Field(default=False, description="Player has submitted orders")
    ready: bool = Field(default=False, description="Player has marked orders as ready")
