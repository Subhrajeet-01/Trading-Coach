# app/api/audit.py
from fastapi import APIRouter, Depends
from app.schemas.audit import AuditRequest, AuditResponse
from app.auth.dependencies import get_current_user
from app.services.audit_service import run_audit

router = APIRouter(tags=["audit"])

@router.post("/audit", response_model=AuditResponse)
async def audit(body: AuditRequest, _: dict = Depends(get_current_user)) -> AuditResponse:
    """Audits an LLM coaching response for hallucinated session IDs."""
    return await run_audit(body.userId, body.coachingResponse)