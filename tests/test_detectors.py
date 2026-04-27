# Quick unit test — run with: uv run python -m pytest tests/test_detectors.py -v
# tests/test_detectors.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
from datetime import datetime, timedelta
from app.schemas.session import Trade
from app.core.pattern_engine import detect_all, detect_revenge_trading
from app.core.feature_engine import extract

def make_trade(**kwargs):
    base = dict(
        tradeId="t1", userId="u1", sessionId="s1", asset="NVDA",
        assetClass="equity", direction="long", entryPrice=100.0,
        exitPrice=98.0, quantity=10, entryAt=datetime(2025,1,6,9,30),
        exitAt=datetime(2025,1,6,10,30), status="closed", outcome="loss",
        pnl=-20.0, planAdherence=4, emotionalState="calm",
        entryRationale=None, revengeFlag=False
    )
    base.update(kwargs)
    return Trade(**base)

def test_revenge_detected():
    t1 = make_trade(tradeId="t1", outcome="loss",
        entryAt=datetime(2025,1,6,9,30), exitAt=datetime(2025,1,6,9,45))
    t2 = make_trade(tradeId="t2", outcome="loss", revengeFlag=True,
        emotionalState="anxious", planAdherence=1,
        entryAt=datetime(2025,1,6,9,46),  # 60s after t1 exit
        exitAt=datetime(2025,1,6,9,50))
    t3 = make_trade(tradeId="t3", outcome="loss", revengeFlag=True,
        emotionalState="fearful", planAdherence=1,
        entryAt=datetime(2025,1,6,9,47),
        exitAt=datetime(2025,1,6,9,52))
    signals = detect_all([t1, t2, t3])
    pathologies = [s.pathology for s in signals]
    assert "revenge_trading" in pathologies, f"Expected revenge_trading, got {pathologies}"
    # Evidence must cite tradeId
    rt = next(s for s in signals if s.pathology=="revenge_trading")
    for ev in rt.evidence:
        assert "tradeId" in ev
        assert "sessionId" in ev
    print("PASS: revenge trading detected with evidence")

def test_clean_trader_no_signals():
    trades = [make_trade(tradeId=f"t{i}", outcome="win",
        planAdherence=5, emotionalState="calm", revengeFlag=False,
        entryAt=datetime(2025,1,6,9,30)+timedelta(hours=i),
        exitAt=datetime(2025,1,6,9,30)+timedelta(hours=i,minutes=90))
        for i in range(5)]
    signals = detect_all(trades)
    assert signals == [], f"Expected no signals, got {[s.pathology for s in signals]}"
    print("PASS: clean trader produces no signals")

if __name__ == "__main__":
    test_revenge_detected()
    test_clean_trader_no_signals()
    print("All detector tests passed.")