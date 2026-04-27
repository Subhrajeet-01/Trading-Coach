# DECISIONS.md

## Project Goal

This project builds a **stateful trading psychology coach** that:

- stores session memory persistently
- retrieves prior sessions for context
- explains coaching decisions with evidence
- detects behavioral patterns from structured trade data
- supports a reproducible evaluation harness

The system is designed as **infrastructure**.

---

## 1. Architecture Choice

### Decision
Use a layered backend architecture:

- `api/` for HTTP routes
- `services/` for orchestration
- `core/` for deterministic logic
- `db/` for persistence
- `auth/` for JWT validation
- `eval/` for offline evaluation

---

## 2. Storage Choice

### Decision
Use **PostgreSQL** for persistent storage.

### Rationale
The memory store must survive container restarts. An in-memory store would be lost on restart and would fail the persistence requirement. PostgreSQL provides durable storage and supports structured queries for sessions, trades, summaries, and detected patterns.

---

## 3. Memory Model

### Decision
Store memory as **structured session summaries** with metrics and tags, and keep raw session records retrievable by exact ID.

### Rationale
The evaluation requires:
- exact retrieval of stored sessions
- traceable references to sessions and trades

Structured storage makes it possible to explain why a coaching message was generated.

---

## 4. Deterministic Pattern Detection

### Decision
Use rule-based feature engineering and pattern detection for behavioral pathologies.

### Rationale
The seed dataset is structured and labeled. Deterministic rules are preferable because they are:
- reproducible
- explainable
- auditable
- suitable for evaluation against ground truth

This reduces the risk of hallucinated behavioral claims.

---

## 5. Feature Engineering

### Decision
Compute session-level features from the trade history, such as:
- revenge trade count
- average plan adherence
- emotional instability
- quick re-entry after loss
- trade frequency
- loss streaks

### Rationale
These features create a bridge between raw trades and pathology labels. They also provide evidence that can be tied back to specific trades.

---

## 6. Evidence-Backed Claims

### Decision
Every behavioral claim must include evidence in the form of:
- `sessionId`
- `tradeId`

### Rationale
The system must not make generic claims. Every coaching explanation must be traceable to the source data so the reviewer can verify it.

---

## 7. Coaching Generation

### Decision
Use the LLM only for wording and coaching tone, not for behavioral reasoning.

---

## 8. Anti-Hallucination Audit

### Decision
Provide a dedicated `/audit` endpoint that checks whether referenced session IDs exist in the database.

### Rationale
The reviewer must be able to verify that the coaching message references real sessions. The audit layer separates generation from verification.

---

## 9. Authentication

### Decision
Use JWT authentication with HS256.

### Rationale
The challenge requires a shared token format across tracks. The authenticated user ID in the token must match the requested user ID in every data access path.

### Enforcement Rule
If `jwt.sub !== requestedUserId`, return HTTP 403.

---

## 10. Error Handling

### Decision
Use standard response codes:

- `401` for missing, invalid, malformed, or expired tokens
- `403` for cross-tenant access attempts

### Rationale
The evaluation explicitly checks that user A cannot access user B’s data. Returning `404` instead of `403` would be incorrect.

---

## 11. Streaming Responses

### Decision
Use Server-Sent Events for streaming coaching messages.

### Rationale
The requirement asks for token-by-token streaming and fast initial response. SSE is a simple fit for one-way streaming and works well with FastAPI.

---

## 12. Evaluation Harness

### Decision
Build a reproducible evaluation script that:
- loads the seed dataset
- computes features
- detects patterns
- aggregates predictions at user level
- generates precision, recall, and F1 per class

### Rationale
The evaluation must be reproducible from the exact provided dataset. A deterministic script is easier to validate than a model-dependent pipeline.

---

## 13. Dependency Management

### Decision
Use `uv` for dependency management and execution.

### Rationale
The project should be reproducible and easy to install. `uv` provides a lockfile-based workflow and faster installs than traditional pip workflows.

---

## 14. Docker Strategy

### Decision
Use Docker Compose to start the full stack with a single command.

### Rationale
The submission requires the system to start without manual steps. Docker Compose is the simplest way to package the API and database together.

---

## 15. Seed Data Handling

### Decision
Treat `nevup_seed_dataset.json` as read-only input.

### Rationale
The evaluation depends on the exact dataset. Modifying or regenerating it would break reproducibility and make results unreliable.

---

## 16. Project Structure

### Decision
Keep the following top-level layout:

- `app/` for application code
- `data/` for the seed dataset
- `eval/` for the evaluation harness
- `scripts/` for utility scripts
- `tests/` for automated checks
- `docker/` for container files

### Rationale
This keeps implementation, evaluation, and deployment separated and easy to understand.

---

## 17. Final System Principle

The system follows this rule:

**All behavioral claims must be grounded in stored evidence.**

That means:
- no invented sessions
- no invented trades
- no unsupported psychological claims
- no cross-user data leakage

The system must be explainable, persistent, and reproducible.