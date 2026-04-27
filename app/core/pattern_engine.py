# app/core/pattern_engine.py
"""All 9 pathology detectors. Every Signal carries cited sessionId+tradeId."""
from typing import NamedTuple, Optional
from app.schemas.session import Trade
from app.core.feature_engine import extract
import statistics

class Signal(NamedTuple):
    pathology: str
    confidence: float
    evidence: list[dict]

def _sig(pathology: str, evidence: list[dict], scale: int = 5) -> Signal:
    """Helper to generate a Signal tuple with a bounded confidence score."""
    return Signal(pathology, min(1.0, len(evidence)/scale), evidence)

def detect_revenge_trading(trades: list[Trade], feats: dict) -> Optional[Signal]:
    """Detects if a user repeatedly trades emotionally shortly after incurring a loss."""
    ev, sorted_t = [], feats["sorted_trades"]
    for i, t in enumerate(sorted_t):
        if not t.revengeFlag:
            continue
        priors = [p for p in sorted_t[:i]
            if p.outcome=="loss"
            and (t.entryAt - p.exitAt).total_seconds() <= 90]
        if priors:
            ev.append({"sessionId":t.sessionId,"tradeId":t.tradeId,
                "triggeredBy":priors[-1].tradeId,
                "secondsAfterLoss":int((t.entryAt-priors[-1].exitAt).total_seconds()),
                "emotionalState":t.emotionalState})
    return _sig("revenge_trading", ev) if len(ev) >= 2 else None

def detect_overtrading(trades: list[Trade], feats: dict) -> Optional[Signal]:
    """Detects excessive trading volume within a single session (e.g., churning)."""
    from collections import defaultdict
    by_s = defaultdict(list)
    for t in trades: by_s[t.sessionId].append(t)
    ev = [{"sessionId":sid,"tradeId":st[0].tradeId,
           "tradeCount":len(st),"reason":f"{len(st)} trades in session"}
          for sid,st in by_s.items() if len(st) >= 12]
    return _sig("overtrading", ev, 3) if ev else None

def detect_fomo_entries(trades: list[Trade], feats: dict) -> Optional[Signal]:
    """Detects trades entered out of greed that resulted in a loss."""
    ev = [{"sessionId":t.sessionId,"tradeId":t.tradeId,
           "emotionalState":t.emotionalState,"planAdherence":t.planAdherence}
          for t in trades
          if t.emotionalState=="greedy" and t.planAdherence==1 and t.outcome=="loss"]
    if len(trades) > 0 and len(ev) / len(trades) > 0.5:
        return _sig("fomo_entries", ev, 4)
    return None

def detect_plan_non_adherence(trades: list[Trade], feats: dict) -> Optional[Signal]:
    """Detects chronic failure to adhere to the trading plan."""
    low = [t for t in trades if t.planAdherence <= 2]
    if not trades or len(low)/len(trades) < 0.75:
        return None
    greedy_low = [t for t in low if t.emotionalState == "greedy"]
    if greedy_low and len(greedy_low) / len(low) > 0.8:
        return None
    ev = [{"sessionId":t.sessionId,"tradeId":t.tradeId,
           "planAdherence":t.planAdherence} for t in low]
    return Signal("plan_non_adherence", len(low)/len(trades), ev)

def detect_premature_exit(trades: list[Trade], feats: dict) -> Optional[Signal]:
    """Detects fearful exits on winning trades that occur too quickly."""
    ev = [{"sessionId":t.sessionId,"tradeId":t.tradeId,
           "holdSeconds":int((t.exitAt-t.entryAt).total_seconds()),"pnl":t.pnl}
          for t in trades
          if t.outcome=="win" and (t.exitAt-t.entryAt).total_seconds() < 600 and t.emotionalState == "fearful"]
    return _sig("premature_exit", ev, 4) if len(ev) >= 5 else None

def detect_loss_running(trades: list[Trade], feats: dict) -> Optional[Signal]:
    """Detects 'hopium' - holding losing trades instead of cutting them."""
    ev = [{"sessionId":t.sessionId,"tradeId":t.tradeId,
           "holdSeconds":int((t.exitAt-t.entryAt).total_seconds()),"pnl":t.pnl}
          for t in trades
          if t.outcome=="loss" and "hoping" in (t.entryRationale or "").lower()]
    return _sig("loss_running", ev, 3) if len(ev) >= 2 else None

def detect_session_tilt(trades: list[Trade], feats: dict) -> Optional[Signal]:
    """Detects emotional tilting driven by external session-level rationalizations."""
    ev = [{"sessionId":t.sessionId,"tradeId":t.tradeId,"reason":"green day rational"}
          for t in trades if t.outcome=="loss" and "green" in (t.entryRationale or "").lower()]
    return _sig("session_tilt", ev, 3) if len(ev) >= 2 else None

def detect_time_of_day_bias(trades: list[Trade], feats: dict) -> Optional[Signal]:
    """Detects severe discrepancies in performance across different times of the day."""
    morning = [t for t in trades if t.entryAt.hour < 12]
    afternoon = [t for t in trades if t.entryAt.hour >= 13]
    if len(morning) >= 5 and len(afternoon) >= 5:
        m_wins = sum(1 for t in morning if t.outcome=="win")
        a_losses = sum(1 for t in afternoon if t.outcome=="loss")
        if m_wins/len(morning) > 0.6 and a_losses/len(afternoon) > 0.6:
            ev = [{"sessionId":morning[0].sessionId,"tradeId":morning[0].tradeId, "hour":morning[0].entryAt.hour,"lossRate":1-m_wins/len(morning)}]
            return _sig("time_of_day_bias", ev, 2)
    return None

def detect_position_sizing_inconsistency(trades: list[Trade], feats: dict) -> Optional[Signal]:
    """Detects erratic position sizing, particularly over-leveraging after a small win."""
    ev = []
    sorted_t = feats.get("sorted_trades", trades)
    last_qty = {}
    last_outcome = {}
    for t in sorted_t:
        asset = t.asset
        qty = t.quantity
        if asset in last_qty and last_outcome[asset] == "win":
            if qty > last_qty[asset] * 8:
                ev.append({"sessionId":t.sessionId,"tradeId":t.tradeId,"notional":t.quantity * t.entryPrice})
        last_qty[asset] = qty
        last_outcome[asset] = t.outcome
    return Signal("position_sizing_inconsistency", 1.0, ev) if ev else None

ALL_DETECTORS = [
    detect_revenge_trading, detect_overtrading, detect_fomo_entries,
    detect_plan_non_adherence, detect_premature_exit, detect_loss_running,
    detect_session_tilt, detect_time_of_day_bias,
    detect_position_sizing_inconsistency,
]

def detect_all(trades: list[Trade]) -> list[Signal]:
    """Runs all detectors on a sequence of trades and features, returning valid signals."""
    feats = extract(trades)
    return [s for d in ALL_DETECTORS if (s := d(trades, feats)) is not None]