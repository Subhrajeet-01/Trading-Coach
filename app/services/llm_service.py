# app/services/llm_service.py
import os
from groq import AsyncGroq
from app.core.pattern_engine import Signal

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    return _client

def _system_prompt(signals: list[Signal], context: dict) -> str:
    session_block = "\n".join(
        f"  - sessionId {s['session_id']}: {str(s.get('summary',''))[:180]}"
        for s in context.get("sessions", [])
    ) or "  No prior sessions stored."

    signal_block = "\n".join(
        f"  - {s.pathology} (confidence {s.confidence:.0%}): "
        f"{len(s.evidence)} instance(s) cited"
        for s in signals
    )
    return f"""You are a trading psychology coach. Be direct, empathetic, and evidence-based.

VERIFIED SESSION HISTORY — only cite sessionIds listed here:
{session_block}

DETECTED SIGNALS THIS SESSION:
{signal_block}

RULES (non-negotiable):
1. Cite sessions as [session: <exact-sessionId>] — only IDs from the list above.
2. Cite trades as [trade: <exact-tradeId>].
3. Never invent a sessionId or tradeId not in the list.
4. If you lack evidence for a claim, say so explicitly.
5. Keep response under 300 words.
6. End with one specific, actionable rule for the trader's next session."""

def _user_prompt(signals: list[Signal]) -> str:
    blocks = []
    for s in signals:
        ev_lines = "\n".join(
            f"    tradeId={e['tradeId']} sessionId={e['sessionId']}: "
            f"{e.get('reason', e.get('emotionalState',''))}"
            for e in s.evidence[:3]
        )
        blocks.append(f"Signal: {s.pathology}\n{ev_lines}")
    return "Verified evidence from this session:\n\n" + "\n\n".join(blocks) + \
           "\n\nGenerate a focused coaching intervention."

async def stream_coaching(signals: list[Signal], context: dict):
    stream = await _get_client().chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=600,
        messages=[
            {"role": "system", "content": _system_prompt(signals, context)},
            {"role": "user", "content": _user_prompt(signals)}
        ],
        stream=True
    )
    async for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content