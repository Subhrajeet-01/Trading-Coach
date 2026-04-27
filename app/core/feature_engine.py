# app/core/feature_engine.py
"""Extracts numeric features from a trade list for pattern matching."""
from app.schemas.session import Trade
from collections import Counter
import statistics

def extract(trades: list[Trade]) -> dict:
    if not trades:
        return {}
    
    sorted_t = sorted(trades, key=lambda t: t.entryAt)
    wins   = [t for t in trades if t.outcome == "win" and t.exitAt]
    losses = [t for t in trades if t.outcome == "loss" and t.exitAt]
    
    # Only calculate durations for closed trades
    holds = [(t.exitAt - t.entryAt).total_seconds() for t in trades if t.exitAt and t.entryAt]
    
    # Filter adherence values
    adherence_vals = [t.planAdherence for t in trades if t.planAdherence is not None]
    
    return {
        "total":           len(trades),
        "win_rate":        len(wins) / len(trades) if trades else 0,
        "avg_adherence":   statistics.mean(adherence_vals) if adherence_vals else 0,
        "revenge_count":   sum(1 for t in trades if t.revengeFlag),
        "avg_hold_wins":   statistics.mean((t.exitAt-t.entryAt).total_seconds()
                            for t in wins) if wins else 0,
        "avg_hold_losses": statistics.mean((t.exitAt-t.entryAt).total_seconds()
                            for t in losses) if losses else 0,
        "emotion_dist":    dict(Counter(t.emotionalState for t in trades if t.emotionalState)),
        "hour_dist":       dict(Counter(t.entryAt.hour for t in trades)),
        "notionals":       [t.quantity * t.entryPrice for t in trades],
        "sorted_trades":   sorted_t,
    }