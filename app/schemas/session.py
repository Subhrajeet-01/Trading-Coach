# app/schemas/session.py
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class Trade(BaseModel):
    """Schema representing an individual executed trade event."""
    tradeId: str
    userId: str
    sessionId: str
    asset: str
    assetClass: Literal["equity","crypto","forex"]
    direction: Literal["long","short"]
    entryPrice: float
    exitPrice: float
    quantity: float
    entryAt: datetime
    exitAt: datetime
    status: str
    outcome: Literal["win","loss"]
    pnl: float
    planAdherence: int
    emotionalState: Literal["calm","anxious","greedy","fearful","neutral"]
    entryRationale: Optional[str] = None
    revengeFlag: bool

class SessionEventsRequest(BaseModel):
    """Incoming request containing a user's bulk block of session trades."""
    userId: str
    sessionId: str
    trades: list[Trade]