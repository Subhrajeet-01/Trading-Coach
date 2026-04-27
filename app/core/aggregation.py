# app/core/aggregation.py
import datetime
from app.schemas.session import Trade
from app.core.pattern_engine import Signal

def build_profile(user_id: str, trades: list[Trade], signals: list[Signal]) -> dict:
    total = len(trades)
    wins = [t for t in trades if getattr(t, 'outcome', None) == "win"]
    
    # Calculate dominant pathologies from signals
    dominant_pathologies = []
    for s in signals:
        dominant_pathologies.append({
            "pathology": s.pathology,
            "confidence": round(s.confidence, 3),
            "evidenceSessions": list(set(e["sessionId"] for e in s.evidence)),
            "evidenceTrades": list(set(e["tradeId"] for e in s.evidence))
        })
    
    # Simple strengths logic
    strengths = []
    if total > 0 and len(wins)/total > 0.6:
        strengths.append("High consistency in trade execution")
    if any(t.planAdherence and t.planAdherence >= 4 for t in trades):
        strengths.append("Strong discipline in following trade plans")

    return {
        "userId": user_id,
        "generatedAt": datetime.datetime.now(datetime.UTC).isoformat(),
        "dominantPathologies": dominant_pathologies,
        "strengths": strengths,
        "peakPerformanceWindow": None # Placeholder for peak performance calc
    }