# app/api/health.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/health")
async def health() -> dict:
    """Simple healthcheck returning service status and version."""
    return {"status": "ok", "version": "1.0.0"}