# app/schemas/session.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID

class Trade(BaseModel):
    """
    Canonical Trade Schema as defined in nevup_openapi.yaml.
    Any deviation breaks interoperability scoring.
    """
    model_config = ConfigDict(populate_by_name=True)

    tradeId: UUID
    userId: UUID
    sessionId: UUID
    asset: str
    assetClass: Literal["equity", "crypto", "forex"]
    direction: Literal["long", "short"]
    entryPrice: float
    quantity: float
    entryAt: datetime
    status: Literal["open", "closed", "cancelled"]
    
    # Nullable fields (Required for Open/Cancelled trades)
    exitPrice: Optional[float] = None
    exitAt: Optional[datetime] = None
    planAdherence: Optional[int] = None
    emotionalState: Optional[Literal["calm", "anxious", "greedy", "fearful", "neutral"]] = None
    entryRationale: Optional[str] = None

    # Computed/AI Fields (defined in 'Trade' component expansion)
    outcome: Optional[Literal["win", "loss"]] = None
    pnl: Optional[float] = None
    revengeFlag: Optional[bool] = False
    
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

class SessionEventsRequest(BaseModel):
    """Request for bulk session processing."""
    userId: UUID
    sessionId: UUID
    trades: list[Trade]