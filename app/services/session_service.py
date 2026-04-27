# app/services/session_service.py
from typing import AsyncGenerator, Tuple
from app.core.pattern_engine import detect_all, Signal
from app.services import memory_service, llm_service
from app.schemas.session import Trade

async def process_session(user_id: str, session_id: str, trades: list[Trade]) -> Tuple[list[Signal], dict]:
    """
    Process a trading session to detect behavioral patterns and retrieve relevant historical context.

    Args:
        user_id (str): Unique identifier for the user.
        session_id (str): Unique identifier for the current session.
        trades (list[Trade]): Sequence of trades executed during the session.

    Returns:
        Tuple[list[Signal], dict]: Detected psychological signals and memory context mapping.
    """
    signals = detect_all(trades)
    context = await memory_service.get_context(
        user_id,
        relevant_to=signals[0].pathology if signals else "general"
    )
    return signals, context

async def stream_coaching(signals: list[Signal], context: dict) -> AsyncGenerator[str, None]:
    """
    Stream a real-time coaching response token-by-token from the LLM based on detected signals.

    Args:
        signals (list[Signal]): The detected behavioral pathologies.
        context (dict): The historical context pulled from the vector memory.

    Yields:
        str: Tokens streaming directly from the LLM.
    """
    async for token in llm_service.stream_coaching(signals, context):
        yield token