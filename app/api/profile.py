# app/api/profile.py
from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import get_current_user, enforce_tenancy
from app.core.pattern_engine import detect_all
from app.core.aggregation import build_profile
from app.schemas.session import Trade
from app.db import repository

router = APIRouter(tags=["Users"])

@router.get("/users/{userId}/profile")
async def get_profile(
    userId: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get behavioral profile for a user (Official NevUp Specification)."""
    enforce_tenancy(userId, current_user)
    
    # 1. Fetch trades from repository
    trade_data = await repository.fetch_trades_for_user(userId)
    if not trade_data:
        # According to spec, return 404 if not found (or return empty profile)
        # But usually, if user exists but has no trades, return an empty profile.
        # Let's check the spec: responses: 404: not found.
        # However, a user without trades still has a profile (empty).
        pass

    trades = [Trade(**t) for t in trade_data]
    
    # 2. Re-detect signals across full history for the profile
    signals = detect_all(trades)
    
    # 3. Build and return the canonical profile
    return build_profile(userId, trades, signals)