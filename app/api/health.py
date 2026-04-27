# app/api/health.py
import datetime
from fastapi import APIRouter
from app.db.repository import get_pool

router = APIRouter(tags=["System"])

@router.get("/health")
async def health_check() -> dict:
    """Health check returning DB connectivity and system state (Canonical spec)."""
    db_status = "disconnected"
    status = "degraded"
    
    try:
        pool = await get_pool()
        # Ping the DB
        await pool.execute("SELECT 1")
        db_status = "connected"
        status = "ok"
    except Exception:
        pass

    return {
        "status": status,
        "dbConnection": db_status,
        "queueLag": 0, # Placeholder for required spec field
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat()
    }