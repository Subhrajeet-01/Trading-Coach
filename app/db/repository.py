# app/db/repository.py
import json
import asyncpg
import os

_pool = None

async def get_pool() -> asyncpg.Pool:
    """Singleton pattern to fetch or initialize the global asyncpg connection pool."""
    global _pool
    if _pool is None:
        url = os.getenv("DATABASE_URL", "").replace(
            "postgresql+asyncpg://", "postgresql://")
        _pool = await asyncpg.create_pool(url, min_size=2, max_size=10)
    return _pool

async def upsert_session(user_id: str, session_id: str, summary: str, metrics: dict, tags: list[str], raw_trades: list[dict]) -> None:
    """Upserts a summary and trade metadata for a given trading session."""
    pool = await get_pool()
    await pool.execute("""
        INSERT INTO session_summaries
            (user_id, session_id, summary, metrics, tags, raw_trades)
        VALUES ($1, $2, $3, $4::jsonb, $5, $6::jsonb)
        ON CONFLICT (session_id) DO UPDATE
            SET summary=$3, metrics=$4, tags=$5, raw_trades=$6
    """, user_id, session_id, summary,
        json.dumps(metrics), tags, json.dumps(raw_trades))

async def fetch_sessions_for_user(user_id: str, limit: int = 5) -> list[dict]:
    """Retrieves a chronological list of recent sessions for the user."""
    pool = await get_pool()
    rows = await pool.fetch("""
        SELECT session_id, summary, metrics, tags, raw_trades, created_at
        FROM session_summaries
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2
    """, user_id, limit)
    return [dict(r) for r in rows]

async def fetch_raw_session(user_id: str, session_id: str) -> dict | None:
    """Retrieves the exact stored record for a single session."""
    pool = await get_pool()
    row = await pool.fetchrow("""
        SELECT * FROM session_summaries
        WHERE user_id=$1 AND session_id=$2
    """, user_id, session_id)
    return dict(row) if row else None

async def session_exists(user_id: str, session_id: str) -> bool:
    """Fast check to verify if a session ID is tracked in the database."""
    pool = await get_pool()
    row = await pool.fetchrow("""
        SELECT 1 FROM session_summaries
        WHERE user_id=$1 AND session_id=$2
    """, user_id, session_id)
    return row is not None

async def upsert_pattern(user_id: str, pattern_id: str, session_ids: list[str], trade_ids: list[str], confidence: float) -> None:
    """Logs an identified behavioral pathology into the pattern tracking engine."""
    pool = await get_pool()
    await pool.execute("""
        INSERT INTO detected_patterns
            (user_id, pattern_id, session_ids, trade_ids, confidence)
        VALUES ($1, $2, $3, $4, $5)
    """, user_id, pattern_id, session_ids, trade_ids, confidence)

async def fetch_patterns_for_user(user_id: str) -> list[dict]:
    """Retrieves all diagnosed behavioral patterns for the user."""
    pool = await get_pool()
    rows = await pool.fetch("""
        SELECT pattern_id, session_ids, trade_ids, confidence
        FROM detected_patterns WHERE user_id=$1
        ORDER BY created_at DESC
    """, user_id)
    return [dict(r) for r in rows]