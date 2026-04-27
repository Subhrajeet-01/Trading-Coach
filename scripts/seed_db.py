# scripts/seed_db.py
import asyncio, json, sys, os
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.repository import upsert_session, upsert_pattern
from app.schemas.session import Trade
from app.core.pattern_engine import detect_all

SEED_PATH = os.path.join(os.path.dirname(__file__), "../data/nevup_seed_dataset.json")

def compute_metrics(session: dict) -> dict:
    trades = session["trades"]
    wins = [t for t in trades if t["outcome"] == "win"]
    ed = {}
    for t in trades:
        ed[t["emotionalState"]] = ed.get(t["emotionalState"], 0) + 1
    return {
        "winRate":             round(len(wins)/len(trades), 3) if trades else 0,
        "avgPlanAdherence":    round(sum(t["planAdherence"] for t in trades)/len(trades),2) if trades else 0,
        "revengeTradeCount":   sum(1 for t in trades if t.get("revengeFlag")),
        "totalPnl":            session.get("totalPnl", 0),
        "tradeCount":          len(trades),
        "emotionalStateDistribution": ed,
    }

async def seed():
    with open(SEED_PATH) as f:
        dataset = json.load(f)

    for trader in dataset["traders"]:
        uid = trader["userId"]
        all_trades = [Trade(**t)
            for s in trader["sessions"] for t in s["trades"]]
        signals = detect_all(all_trades)

        for session in trader["sessions"]:
            metrics = compute_metrics(session)
            pathology_tags = [s.pathology for s in signals]
            summary = (
                f"Session {session['date'][:10]} | "
                f"trades={session['tradeCount']} pnl={session['totalPnl']} "
                f"winRate={session['winRate']} | "
                f"pathologies={','.join(pathology_tags) or 'none'}"
            )
            await upsert_session(
                uid, session["sessionId"], summary,
                metrics, pathology_tags, session["trades"]
            )

        for s in signals:
            await upsert_pattern(
                uid, s.pathology,
                list({e["sessionId"] for e in s.evidence}),
                [e["tradeId"] for e in s.evidence],
                s.confidence
            )

        print(f"Seeded {trader['name']}: "
              f"{len(trader['sessions'])} sessions, "
              f"signals={[s.pathology for s in signals]}")

    print("Seed complete.")

if __name__ == "__main__":
    asyncio.run(seed())