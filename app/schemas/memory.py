# app/schemas/memory.py
from pydantic import BaseModel
from typing import Optional

class BehavioralMetrics(BaseModel):
    """Metadata surrounding a trader's performance over a specific session."""
    winRate: float
    avgPlanAdherence: float
    revengeTradeCount: int
    totalPnl: float
    tradeCount: int
    emotionalStateDistribution: dict[str, int]
    avgTimeBetweenLossAndNextEntry: Optional[float] = None

class StoreSummaryRequest(BaseModel):
    """Schema for pushing a finalized session embedding and summary into Postgres."""
    summary: str
    metrics: BehavioralMetrics
    tags: list[str]
    raw_trades: list[dict] = []

class ContextResponse(BaseModel):
    """Response returned when the AI pulls contextual memory arrays."""
    sessions: list[dict]
    patternIds: list[str]