# app/api/trades.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.session import Trade
from app.auth.dependencies import get_current_user
from app.db import repository

router = APIRouter(tags=["Trades"])

@router.post("/trades", response_model=Trade)
async def create_trade(
    body: Trade,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Submit a new trade. Idempotent on tradeId."""
    if str(body.userId) != str(current_user["sub"]):
        raise HTTPException(403, detail={"error": "FORBIDDEN", "message": "Cross-tenant access denied."})
    
    # Store in DB
    trade_record = await repository.upsert_trade(body.model_dump())
    return trade_record

@router.get("/trades/{tradeId}", response_model=Trade)
async def get_trade(
    tradeId: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get a single trade by ID."""
    trade = await repository.fetch_trade(tradeId)
    if not trade:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Trade not found"})
    
    if str(trade["userId"]) != str(current_user["sub"]):
        raise HTTPException(403, detail={"error": "FORBIDDEN", "message": "Access denied"})
        
    return trade
