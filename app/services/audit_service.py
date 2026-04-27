# app/services/audit_service.py
import re
from app.services.memory_service import exists
from app.schemas.audit import AuditResponse, AuditResult

SID_RE = re.compile(
    r'\[session:\s*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}'
    r'-[0-9a-f]{4}-[0-9a-f]{12})\]', re.IGNORECASE)

async def run_audit(user_id: str, text: str) -> AuditResponse:
    cited = SID_RE.findall(text)
    results = []
    for sid in set(cited):
        found = await exists(user_id, sid)
        results.append(AuditResult(
            sessionId=sid,
            status="found" if found else "not-found"
        ))
    hallucinated = [r for r in results if r.status=="not-found"]
    return AuditResponse(
        totalCitations=len(cited),
        unique=len(set(cited)),
        results=results,
        hallucinated=hallucinated
    )
    