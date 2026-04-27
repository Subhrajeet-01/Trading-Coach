# app/api/session.py
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.auth.dependencies import get_current_user
from app.services import session_service, memory_service
from app.schemas.session import Trade

router = APIRouter(tags=["Sessions"])

@router.get("/sessions/{sessionId}")
async def get_session(
    sessionId: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get session summary with full trade list (Canonical spec)."""
    # Fetch from memory service (which now points to new DB schema)
    session = await memory_service.get_raw(current_user["sub"], sessionId)
    if not session:
        raise HTTPException(404, detail={"error":"NOT_FOUND", "message":"Session not found"})
    
    return session

@router.get("/sessions/{sessionId}/coaching")
async def stream_coaching(
    sessionId: str,
    current_user: dict = Depends(get_current_user)
) -> StreamingResponse:
    """
    Stream AI coaching message (SSE) - Official Track 3 Format.
    Streams json tokens with index.
    """
    # 1. Fetch trades for this session
    session_data = await memory_service.get_raw(current_user["sub"], sessionId)
    if not session_data:
        raise HTTPException(404, detail={"error":"NOT_FOUND", "message":"Session not found"})
    
    trades = [Trade(**t) for t in session_data.get("trades", [])]
    
    # 2. Trigger pattern detection and context retrieval
    signals, context = await session_service.process_session(
        current_user["sub"], sessionId, trades)

    async def sse_generator():
        full_msg = []
        try:
            index = 0
            async for token in session_service.stream_coaching(signals, context):
                full_msg.append(token)
                yield f"event: token\ndata: {json.dumps({'token': token, 'index': index})}\n\n"
                index += 1
            
            yield f"event: done\ndata: {json.dumps({'fullMessage': ''.join(full_msg)})}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )