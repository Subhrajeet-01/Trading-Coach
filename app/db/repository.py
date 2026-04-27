# app/db/repository.py
import json
import asyncpg
import os
from uuid import UUID
from datetime import datetime

_pool = None

async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        raw_url = os.getenv("DATABASE_URL", "")
        # Robust parsing for production environments (Render/Heroku/Standard)
        url = raw_url.replace("postgresql+asyncpg://", "postgresql://")
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        
        _pool = await asyncpg.create_pool(url, min_size=2, max_size=10)
    return _pool

def _parse_dt(dt_val):
    if isinstance(dt_val, str):
        # Handle the 'Z' suffix specifically for older isoformat versions or certain formats
        return datetime.fromisoformat(dt_val.replace("Z", "+00:00"))
    return dt_val

async def upsert_trade(t: dict) -> dict:
    """Idempotent trade submission as required by the NevUp spec."""
    pool = await get_pool()
    
    entry_at = _parse_dt(t["entryAt"])
    exit_at = _parse_dt(t["exitAt"]) if t.get("exitAt") else None

    row = await pool.fetchrow("""
        INSERT INTO trades
            (id, user_id, session_id, asset, asset_class, direction, 
             entry_price, exit_price, quantity, entry_at, exit_at, 
             status, plan_adherence, emotional_state, entry_rationale,
             outcome, pnl, revenge_flag)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
        ON CONFLICT (id) DO UPDATE SET updated_at = now()
        RETURNING id as "tradeId", user_id as "userId", session_id as "sessionId",
                asset, asset_class as "assetClass", direction, 
                entry_price as "entryPrice", exit_price as "exitPrice", quantity, 
                entry_at as "entryAt", exit_at as "exitAt", 
                status, plan_adherence as "planAdherence", emotional_state as "emotionalState", 
                entry_rationale as "entryRationale", outcome, pnl, revenge_flag as "revengeFlag"
    """, UUID(str(t["tradeId"])), UUID(str(t["userId"])), UUID(str(t["sessionId"])),
        t["asset"], t["assetClass"], t["direction"],
        t["entryPrice"], t.get("exitPrice"), t["quantity"],
        entry_at, exit_at, t["status"],
        t.get("planAdherence"), t.get("emotionalState"), t.get("entryRationale"),
        t.get("outcome"), t.get("pnl"), t.get("revengeFlag", False))
    return dict(row)

async def fetch_trade(trade_id: str) -> dict | None:
    pool = await get_pool()
    row = await pool.fetchrow("""
        SELECT id as "tradeId", user_id as "userId", session_id as "sessionId",
               asset, asset_class as "assetClass", direction, entry_price as "entryPrice",
               exit_price as "exitPrice", quantity, entry_at as "entryAt", exit_at as "exitAt",
               status, plan_adherence as "planAdherence", emotional_state as "emotionalState",
               entry_rationale as "entryRationale", outcome, pnl, revenge_flag as "revengeFlag"
        FROM trades WHERE id = $1
    """, UUID(str(trade_id)))
    return dict(row) if row else None

async def upsert_session(user_id: str, session_id: str, notes: str, trade_count: int, win_rate: float, total_pnl: float) -> None:
    pool = await get_pool()
    await pool.execute("""
        INSERT INTO session_summaries
            (user_id, session_id, notes, trade_count, win_rate, total_pnl)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (session_id) DO UPDATE
            SET notes=$3, trade_count=$4, win_rate=$5, total_pnl=$6
    """, UUID(str(user_id)), UUID(str(session_id)), notes, trade_count, win_rate, total_pnl)

async def fetch_raw_session(user_id: str, session_id: str) -> dict | None:
    """Retrieves session summary + full trade list (Canonical format)."""
    pool = await get_pool()
    s_row = await pool.fetchrow("""
        SELECT session_id as "sessionId", user_id as "userId", date, notes, 
               trade_count as "tradeCount", win_rate as "winRate", total_pnl as "totalPnl"
        FROM session_summaries
        WHERE user_id=$1 AND session_id=$2
    """, UUID(str(user_id)), UUID(str(session_id)))
    
    if not s_row:
        return None

    t_rows = await pool.fetch("""
        SELECT id as "tradeId", user_id as "userId", session_id as "sessionId",
               asset, asset_class as "assetClass", direction, entry_price as "entryPrice",
               exit_price as "exitPrice", quantity, entry_at as "entryAt", exit_at as "exitAt",
               status, plan_adherence as "planAdherence", emotional_state as "emotionalState",
               entry_rationale as "entryRationale", outcome, pnl, revenge_flag as "revengeFlag"
        FROM trades
        WHERE session_id = $1
    """, UUID(str(session_id)))
    
    res = dict(s_row)
    res["trades"] = [dict(r) for r in t_rows]
    return res

async def session_exists(user_id: str, session_id: str) -> bool:
    pool = await get_pool()
    row = await pool.fetchrow("SELECT 1 FROM session_summaries WHERE user_id=$1 AND session_id=$2", UUID(str(user_id)), UUID(str(session_id)))
    return row is not None

async def upsert_pattern(user_id: str, pattern_id: str, session_ids: list[str], trade_ids: list[str], confidence: float) -> None:
    pool = await get_pool()
    await pool.execute("""
        INSERT INTO detected_patterns
            (user_id, pattern_id, session_ids, trade_ids, confidence)
        VALUES ($1, $2, $3::uuid[], $4::uuid[], $5)
    """, UUID(str(user_id)), pattern_id, [UUID(str(s)) for s in session_ids], [UUID(str(t)) for t in trade_ids], confidence)

async def fetch_patterns_for_user(user_id: str) -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch("""
        SELECT pattern_id as pathology, session_ids as "evidenceSessions", 
               trade_ids as "evidenceTrades", confidence
        FROM detected_patterns WHERE user_id=$1
        ORDER BY created_at DESC
    """, UUID(str(user_id)))
    return [dict(r) for r in rows]

async def fetch_sessions_for_user(user_id: str, limit: int = 10, offset: int = 0) -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch("""
        SELECT session_id as "sessionId", user_id as "userId", date, notes,
               trade_count as "tradeCount", win_rate as "winRate", total_pnl as "totalPnl"
        FROM session_summaries
        WHERE user_id = $1
        ORDER BY date DESC
        LIMIT $2 OFFSET $3
    """, UUID(str(user_id)), limit, offset)
    return [dict(r) for r in rows]

async def fetch_trades_for_user(user_id: str) -> list[dict]:
    pool = await get_pool()
    rows = await pool.fetch("""
        SELECT id as "tradeId", user_id as "userId", session_id as "sessionId",
               asset, asset_class as "assetClass", direction, entry_price as "entryPrice",
               exit_price as "exitPrice", quantity, entry_at as "entryAt", exit_at as "exitAt",
               status, plan_adherence as "planAdherence", emotional_state as "emotionalState",
               entry_rationale as "entryRationale", outcome, pnl, revenge_flag as "revengeFlag"
        FROM trades WHERE user_id = $1
        ORDER BY entry_at DESC
    """, UUID(str(user_id)))
    return [dict(r) for r in rows]