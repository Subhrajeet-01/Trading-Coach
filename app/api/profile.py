# app/api/profile.py
from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user, enforce_tenancy
from app.core.pattern_engine import detect_all
from app.core.aggregation import build_profile
from app.schemas.session import Trade as TradeSchema
from pydantic import BaseModel

class ProfileRequest(BaseModel):
    trades: list[TradeSchema]

router = APIRouter(tags=["profile"])

@router.post("/profile/{userId}")
async def get_profile(
    userId: str,
    body: ProfileRequest,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Generates a complete behavioral profile from a raw list of historical trades."""
    enforce_tenancy(userId, current_user)
    signals = detect_all(body.trades)
    return build_profile(userId, body.trades, signals)