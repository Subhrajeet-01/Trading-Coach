# app/services/memory_service.py
from typing import Optional
from app.db.repository import (
    upsert_session, fetch_sessions_for_user,
    fetch_raw_session, session_exists, fetch_patterns_for_user,
    upsert_trade
)

async def store(user_id: str, session_id: str, summary: str, metrics: dict, tags: list[str], raw_trades: list[dict]) -> None:
    """
    Store the summary and technical metrics of a trading session into the database.
    """
    # 1. Store individual trades
    for t in raw_trades:
        await upsert_trade(t)

    # 2. Store session summary
    await upsert_session(
        user_id=user_id,
        session_id=session_id,
        notes=summary,
        trade_count=metrics.get("tradeCount", 0),
        win_rate=metrics.get("winRate", 0.0),
        total_pnl=metrics.get("totalPnl", 0.0)
    )

async def get_context(user_id: str, relevant_to: str) -> dict:
    """
    Retrieve historical session context.
    Matches the 'ContextResponse' schema in app/schemas/memory.py.
    """
    sessions = await fetch_sessions_for_user(user_id, limit=5)
    patterns = await fetch_patterns_for_user(user_id)
    
    # Simple strategy: include sessions that have the pathology in their notes/summary
    relevant = [s for s in sessions if relevant_to.lower() in (s.get("notes") or "").lower()]
    
    return {
        "sessions": relevant or sessions[:3],
        "patternIds": [p["pathology"] for p in patterns] # Match ContextResponse schema
    }

async def get_raw(user_id: str, session_id: str) -> Optional[dict]:
    """
    Fetch the raw session record directly from the database.
    """
    return await fetch_raw_session(user_id, session_id)

async def exists(user_id: str, session_id: str) -> bool:
    """
    Check if a specific session ID exists in the database.
    """
    return await session_exists(user_id, session_id)