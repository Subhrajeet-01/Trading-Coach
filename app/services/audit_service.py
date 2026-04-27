# app/services/audit_service.py
import re
from app.services.memory_service import exists
from app.schemas.audit import AuditResponse, AuditResult

CIT_RE = re.compile(r'\[(session|trade):\s*([a-z0-9\-]+)\]', re.IGNORECASE)

async def run_audit(user_id: str, text: str) -> AuditResponse:
    matches = CIT_RE.findall(text)
    total_cited = len(matches)
    
    unique_matches = set(matches)
    results = []
    
    for ctype, cid in unique_matches:
        # Verify against memory service (currently check focused on sessions)
        found = await exists(user_id, cid)
        
        results.append(AuditResult(
            sessionId=cid, # Repurposing field or using generic identifier
            status="found" if found else "not-found"
        ))
        
    hallucinated = [r for r in results if r.status=="not-found"]
    return AuditResponse(
        totalCitations=total_cited,
        unique=len(unique_matches),
        results=results,
        hallucinated=hallucinated
    )
    