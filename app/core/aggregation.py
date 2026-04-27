# app/core/aggregation.py
"""Builds a structured profile from signals. Every claim cites evidence."""
from app.schemas.session import Trade
from app.core.pattern_engine import Signal

def build_profile(user_id: str, trades: list[Trade], signals: list[Signal]) -> dict:
    total = len(trades)
    wins  = [t for t in trades if t.outcome == "win"]
    return {
        "userId":              user_id,
        "totalTrades":         total,
        "winRate":             round(len(wins)/total, 3) if total else 0,
        "avgPlanAdherence":    round(sum(t.planAdherence for t in trades)/total,2) if total else 0,
        "totalPnl":            round(sum(t.pnl for t in trades), 2),
        "detectedPathologies": [s.pathology for s in signals],
        "pathologyDetails": [
            {
                "pathology":  s.pathology,
                "confidence": round(s.confidence, 3),
                "evidence":   s.evidence   # cited sessionId + tradeId per item
            }
            for s in signals
        ]
    }