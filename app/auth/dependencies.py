import uuid
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.jwt_handler import verify_jwt

security = HTTPBearer(auto_error=False)

def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Extracts and verifies the JWT token from the Authorization header."""
    if not creds:
        raise HTTPException(401, detail={
            "error":"UNAUTHORIZED",
            "message":"Missing Authorization header",
            "traceId": str(uuid.uuid4())
        })
    return verify_jwt(creds.credentials)

def enforce_tenancy(user_id: str, current_user: dict) -> dict:
    """Ensures the authenticated user is only accessing their own nested resources."""
    if str(current_user["sub"]) != str(user_id):
        raise HTTPException(403, detail={
            "error":"FORBIDDEN",
            "message":"Cross-tenant access denied.",
            "traceId": str(uuid.uuid4())
        })
    return current_user