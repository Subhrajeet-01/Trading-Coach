# app/api/memory.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.memory import StoreSummaryRequest, ContextResponse
from app.auth.dependencies import get_current_user, enforce_tenancy
from app.services import memory_service

router = APIRouter(prefix="/memory", tags=["memory"])

@router.put("/{userId}/sessions/{sessionId}")
async def put_session(
    userId: str, sessionId: str,
    body: StoreSummaryRequest,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Stores a finalized session summary, tracking behavioral metrics permanently."""
    enforce_tenancy(userId, current_user)
    await memory_service.store(
        userId, sessionId,
        body.summary, body.metrics.model_dump(),
        body.tags, body.raw_trades
    )
    return {"status": "stored", "sessionId": sessionId}

@router.get("/{userId}/context", response_model=ContextResponse)
async def get_context(
    userId: str, relevantTo: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Retrieves high-context past performance data relevant to a flagged signal."""
    enforce_tenancy(userId, current_user)
    return await memory_service.get_context(userId, relevantTo)

@router.get("/{userId}/sessions/{sessionId}")
async def get_session(
    userId: str, sessionId: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Fetches a raw historical session strictly for hallucination verification."""
    enforce_tenancy(userId, current_user)
    result = await memory_service.get_raw(userId, sessionId)
    if not result:
        raise HTTPException(404, detail={"error":"NOT_FOUND",
            "message":"Session not found"})
    return result