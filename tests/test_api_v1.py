# tests/test_api_v1.py
import pytest
import requests
import uuid
import time

BASE_URL = "http://127.0.0.1:8000"
USER_ID = "f412f236-4edc-47a2-8f54-8763a6ed2ce8"
SESSION_ID = "57651b39-b4f9-496c-9afb-36535f841fb4"

@pytest.fixture(scope="session")
def auth_headers():
    """Obtain a valid JWT token for the session."""
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "userId": USER_ID,
        "name": "QuickTest User"
    })
    assert resp.status_code == 200
    token = resp.json()["token"]
    return {"Authorization": f"Bearer {token}"}

def test_health_check():
    """Verify system health schema compliance."""
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "dbConnection" in data

def test_trade_lifecycle(auth_headers):
    """Test submitting and then retrieving a trade."""
    trade_id = str(uuid.uuid4())
    trade_data = {
        "tradeId": trade_id,
        "userId": USER_ID,
        "sessionId": SESSION_ID,
        "asset": "BTC/USD",
        "assetClass": "crypto",
        "direction": "long",
        "entryPrice": 50000.0,
        "quantity": 1.0,
        "entryAt": "2025-01-01T10:00:00Z",
        "status": "open"
    }
    
    # 1. Create
    create_resp = requests.post(f"{BASE_URL}/trades", json=trade_data, headers=auth_headers)
    assert create_resp.status_code == 200
    
    # 2. Retrieve
    get_resp = requests.get(f"{BASE_URL}/trades/{trade_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["tradeId"] == trade_id

def test_session_detail(auth_headers):
    """Test relational session detail retrieval."""
    resp = requests.get(f"{BASE_URL}/sessions/{SESSION_ID}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["sessionId"] == SESSION_ID
    assert "trades" in data
    assert isinstance(data["trades"], list)

def test_behavioral_profile(auth_headers):
    """Test generating a psychological profile for the user."""
    resp = requests.get(f"{BASE_URL}/users/{USER_ID}/profile", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["userId"] == USER_ID
    assert "dominantPathologies" in data

def test_memory_context(auth_headers):
    """Test historical context retrieval through memory service."""
    path = f"/memory/{USER_ID}/context?relevantTo=revenge_trading"
    resp = requests.get(f"{BASE_URL}{path}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "sessions" in data
    assert "patternIds" in data

def test_hallucination_audit(auth_headers):
    """Test the AI hallucination audit endpoint."""
    payload = {
        "userId": USER_ID,
        "coachingResponse": f"You did great in session {SESSION_ID}."
    }
    resp = requests.post(f"{BASE_URL}/audit", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    assert "totalCitations" in resp.json()

def test_sse_streaming_connectivity(auth_headers):
    """Test establishing a connection to the SSE coaching stream."""
    url = f"{BASE_URL}/sessions/{SESSION_ID}/coaching"
    with requests.get(url, headers=auth_headers, stream=True, timeout=5) as r:
        assert r.status_code == 200
        # Check first line of stream to ensure it's SSE
        first_line = next(r.iter_lines()).decode()
        assert "event:" in first_line or "data:" in first_line
