# scripts/seed_db.py
import asyncio, json, sys, os
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.repository import get_pool, upsert_session, upsert_pattern
from app.schemas.session import Trade
from app.core.pattern_engine import detect_all

SEED_PATH = os.path.join(os.path.dirname(__file__), "../data/nevup_seed_dataset.json")
INIT_SQL_PATH = os.path.join(os.path.dirname(__file__), "../init.sql")

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

async def init_schema():
    print("Checking database schema...")
    pool = await get_pool()
    if not os.path.exists(INIT_SQL_PATH):
        print(f"Warning: {INIT_SQL_PATH} not found. Skipping schema init.")
        return
        
    with open(INIT_SQL_PATH) as f:
        sql = f.read()
    
    # Execute init.sql line by line or as a block
    # Note: asyncpg execute can run multiple statements
    try:
        await pool.execute(sql)
        print("Schema initialized successfully.")
    except Exception as e:
        print(f"Error initializing schema: {e}")

async def seed():
    # 1. Initialize Schema
    await init_schema()
    
    # 2. Check for existing data
    pool = await get_pool()
    count = await pool.fetchval("SELECT count(*) FROM session_summaries")
    if count > 0:
        print(f"Database already has {count} sessions. Skipping seed.")
        return

    print("Seeding database from dataset...")
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
            try:
                await upsert_pattern(
                    uid, s.pathology,
                    list({e["sessionId"] for e in s.evidence}),
                    [e["tradeId"] for e in s.evidence],
                    s.confidence
                )
            except Exception as e:
                # In case of duplicates or other issues in patterns
                print(f"Skipping pattern {s.pathology} for {uid}: {e}")

        print(f"Seeded {trader['name']}: "
              f"{len(trader['sessions'])} sessions, "
              f"signals={[s.pathology for s in signals]}")

    print("Seed complete.")

if __name__ == "__main__":
    asyncio.run(seed())