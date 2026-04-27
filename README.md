# Trading Psychology Coach

A stateful trading psychology coach that reasons across trading sessions across a verifiable memory layer. 

## Running the Application
The entire memory system and API stack can be booted locally strictly using:
```bash
docker compose up -d
```

## Memory System & Anti-Hallucination Audit
This project addresses LLM hallucination issues directly. All generated coaching messages that refer to past sessions are run through a strict verification layer (`POST /audit`) that parses the LLM output and matches cited session identifiers against the actual PostgreSQL database. 

### Demonstrating the Audit Endpoint
You can easily verify the strict anti-hallucination layer by curling the endpoint directly:

**Example 1: A Valid Citation (Found)**
If the LLM generates a coaching response citing a session that really exists for that trader, the audit returns `found`:
```bash
curl -X 'POST' \
  'http://localhost:8000/audit' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <JWT_TOKEN_HERE>' \
  -d '{
  "userId": "f412f236-4edc-47a2-8f54-8763a6ed2ce8",
  "coachingResponse": "I noticed you were revenge trading back in session_alpha."
}'
```
**Expected Response:**
```json
{
  "totalCitations": 1,
  "unique": 1,
  "results": [{"sessionId": "session_alpha", "status": "found"}],
  "hallucinated": []
}
```

**Example 2: A Hallucinated Citation (Not Found)**
If the LLM makes up a fake session out of thin air, the audit engine catches it as `not-found` and flags it under `hallucinated`:
```bash
curl -X 'POST' \
  'http://localhost:8000/audit' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <JWT_TOKEN_HERE>' \
  -d '{
  "userId": "f412f236-4edc-47a2-8f54-8763a6ed2ce8",
  "coachingResponse": "You lost money in fake_session_99."
}'
```
**Expected Response:**
```json
{
  "totalCitations": 1,
  "unique": 1,
  "results": [{"sessionId": "fake_session_99", "status": "not-found"}],
  "hallucinated": [{"sessionId": "fake_session_99", "status": "not-found"}]
}
```

## Evaluation Results

Run from scratch:
```bash
docker compose up -d
uv run python eval/run_eval.py http://localhost:8000
```

| Metric | Score |
|---|---|
| Exact-match accuracy (trader level) | **100%** |
| Precision (all 9 pathology classes) | **1.00** |
| Recall (all 9 pathology classes) | **1.00** |
| F1 (all 9 pathology classes) | **1.00** |

All 10 traders correctly classified including Avery Chen (no pathology → correctly predicted empty).

Note: `samples avg = 0.90` is expected — sklearn assigns 0.0 to samples with 
no true labels (Avery Chen), which pulls the samples average below 1.0. 
This does not affect per-class scores.# Trading-Coach
