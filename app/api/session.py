# app/api/session.py
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.session import SessionEventsRequest
from app.auth.dependencies import get_current_user
from app.services import session_service

router = APIRouter(tags=["session"])

@router.post("/session/events")
async def session_events(
    body: SessionEventsRequest,
    current_user: dict = Depends(get_current_user)
) -> StreamingResponse | dict:
    """Streams token-by-token behavioral coaching based on live trade events."""
    if body.userId != current_user["sub"]:
        raise HTTPException(403, detail={"error":"FORBIDDEN",
            "message":"Cross-tenant access denied.",
            "traceId":str(uuid.uuid4())})

    signals, context = await session_service.process_session(
        body.userId, body.sessionId, body.trades)

    if not signals:
        return {"message":"No behavioral signals detected","signals":[]}

    async def sse():
        async for token in session_service.stream_coaching(signals, context):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(sse(),
        media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})