# scripts/seed_db.py
import asyncio, json, sys, os
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.repository import get_pool, upsert_session, upsert_pattern, upsert_trade
from app.schemas.session import Trade
from app.core.pattern_engine import detect_all

SEED_PATH = os.path.join(os.path.dirname(__file__), "../data/nevup_seed_dataset.json")
INIT_SQL_PATH = os.path.join(os.path.dirname(__file__), "../init.sql")

async def init_schema():
    print("Checking database schema...")
    pool = await get_pool()
    if not os.path.exists(INIT_SQL_PATH):
        print(f"Warning: {INIT_SQL_PATH} not found. Skipping schema init.")
        return
        
    with open(INIT_SQL_PATH) as f:
        sql = f.read()
    
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
        
        # Collect all trades for pattern detection
        all_trader_trades = []
        for session in trader["sessions"]:
            for t_data in session["trades"]:
                all_trader_trades.append(Trade(**t_data))

        # Detect patterns across full history
        signals = detect_all(all_trader_trades)

        for session in trader["sessions"]:
            # 1. Seed Individual Trades
            for t_data in session["trades"]:
                await upsert_trade(t_data)
            
            # 2. Seed Session Summary
            notes = f"Seed session from {session['date'][:10]}."
            await upsert_session(
                user_id=uid,
                session_id=session["sessionId"],
                notes=notes,
                trade_count=session["tradeCount"],
                win_rate=session["winRate"],
                total_pnl=session["totalPnl"]
            )

        # 3. Seed Detected Patterns (Memory)
        for s in signals:
            try:
                await upsert_pattern(
                    uid, s.pathology,
                    list({e["sessionId"] for e in s.evidence}),
                    [e["tradeId"] for e in s.evidence],
                    s.confidence
                )
            except Exception as e:
                print(f"Skipping pattern {s.pathology} for {uid}: {e}")

        print(f"Seeded {trader['name']}: {len(trader['sessions'])} sessions")

    print("Seed complete.")

if __name__ == "__main__":
    asyncio.run(seed())