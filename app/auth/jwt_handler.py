import hmac, hashlib, base64, json, time, uuid, os
from app.utils.constants import JWT_SECRET

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _b64url_decode(s: str) -> bytes:
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)

def issue_jwt(user_id: str, name: str | None = None) -> str:
    header  = _b64url_encode(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
    now     = int(time.time())
    payload = _b64url_encode(json.dumps({
        "sub": user_id, "iat": now,
        "exp": now + 86400, "role": "trader",
        **({"name": name} if name else {})
    }).encode())
    sig = _b64url_encode(
        hmac.new(JWT_SECRET.encode(),
            f"{header}.{payload}".encode(), hashlib.sha256).digest()
    )
    return f"{header}.{payload}.{sig}"

def verify_jwt(token: str) -> dict:
    from fastapi import HTTPException
    trace_id = str(uuid.uuid4())

    parts = token.strip().split(".")
    if len(parts) != 3:
        raise HTTPException(401, detail={"error":"INVALID_TOKEN",
            "message":"Malformed JWT","traceId":trace_id})

    h, p, sig = parts
    expected = _b64url_encode(
        hmac.new(JWT_SECRET.encode(),
            f"{h}.{p}".encode(), hashlib.sha256).digest()
    )
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(401, detail={"error":"INVALID_TOKEN",
            "message":"Bad signature","traceId":trace_id})

    try:
        payload = json.loads(_b64url_decode(p))
    except Exception:
        raise HTTPException(401, detail={"error":"INVALID_TOKEN",
            "message":"Bad payload","traceId":trace_id})

    for c in ("sub","iat","exp","role"):
        if c not in payload:
            raise HTTPException(401, detail={"error":"MISSING_CLAIM",
                "message":f"Missing: {c}","traceId":trace_id})

    if payload["exp"] <= int(time.time()):
        raise HTTPException(401, detail={"error":"TOKEN_EXPIRED",
            "message":"Token expired","traceId":trace_id})

    return payload