# app/services/memory_service.py
from typing import Optional
from app.db.repository import (
    upsert_session, fetch_sessions_for_user,
    fetch_raw_session, session_exists, fetch_patterns_for_user
)

async def store(user_id: str, session_id: str, summary: str, metrics: dict, tags: list[str], raw_trades: list[dict]) -> None:
    """
    Store the summary and technical metrics of a trading session into the database.

    Args:
        user_id (str): The user's unique identifier.
        session_id (str): The session's unique identifier.
        summary (str): The LLM-generated summary of the session.
        metrics (dict): Performance metrics and emotional distributions.
        tags (list[str]): Behavioral pathology tags.
        raw_trades (list[dict]): The raw trades associated with the session.
    """
    await upsert_session(user_id, session_id, summary, metrics, tags, raw_trades)

async def get_context(user_id: str, relevant_to: str) -> dict:
    """
    Retrieve historical session context based on tag relevance.

    Args:
        user_id (str): The user's unique identifier.
        relevant_to (str): The behavioral tag to search for in past sessions.

    Returns:
        dict: A dictionary containing relevant past sessions and historical pattern IDs.
    """
    sessions = await fetch_sessions_for_user(user_id, limit=5)
    patterns = await fetch_patterns_for_user(user_id)
    
    # Tag-based relevance filter
    relevant = [s for s in sessions if any(relevant_to in t for t in s.get("tags", []))]
    
    return {
        "sessions": relevant or sessions[:3],
        "patternIds": [p["pattern_id"] for p in patterns]
    }

async def get_raw(user_id: str, session_id: str) -> Optional[dict]:
    """
    Fetch the raw, unadulterated session record directly from the database.
    """
    return await fetch_raw_session(user_id, session_id)

async def exists(user_id: str, session_id: str) -> bool:
    """
    Check if a specific session ID exists in the database for the given user.
    """
    return await session_exists(user_id, session_id)