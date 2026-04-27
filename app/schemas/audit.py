# app/schemas/audit.py
from pydantic import BaseModel

class AuditRequest(BaseModel):
    """Body containing LLM-generated string checking for bad citations."""
    userId: str
    coachingResponse: str

class AuditResult(BaseModel):
    """Represents the verification of a single sessionId cited by the LLM."""
    sessionId: str
    status: str   # "found" | "not-found"

class AuditResponse(BaseModel):
    """Payload representing exactly which cited sessions were real vs hallucinated."""
    totalCitations: int
    unique: int
    results: list[AuditResult]
    hallucinated: list[AuditResult]