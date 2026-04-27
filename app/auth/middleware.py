import time, uuid, json, logging
from fastapi import Request
from app.auth.jwt_handler import verify_jwt

logger = logging.getLogger("nevup")

async def logging_middleware(request: Request, call_next):
    """Intercepts requests to log latencies, paths, and status codes for observability."""
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id
    start = time.time()
    response = await call_next(request)
    user_id = None
    try:
        auth = request.headers.get("Authorization","")
        if auth.startswith("Bearer "):
            user_id = verify_jwt(auth[7:]).get("sub")
    except Exception:
        pass
    logger.info(json.dumps({
        "traceId": trace_id, "userId": user_id,
        "latency": int((time.time()-start)*1000),
        "statusCode": response.status_code,
        "path": str(request.url.path),
    }))
    response.headers["X-Trace-Id"] = trace_id
    return response