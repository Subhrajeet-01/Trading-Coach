# Architectural Decisions & Design Patterns

This document defines the architectural principles, system design choices, and implementation patterns used in the Trading Psychology Coach. The system is designed to provide stateful behavioral coaching with strict guarantees around reproducibility, auditability, and non-hallucinatory outputs.

---

## 1. System Architecture

A **layered architecture** is used to enforce separation of concerns and maintain modularity.

### Layers

- **API Layer (`app/api/`)**
  - Handles HTTP routing, request validation, and response serialization.
  - Built using FastAPI.

- **Service Layer (`app/services/`)**
  - Orchestrates workflows across core logic, database operations, and external integrations.

- **Core Layer (`app/core/`)**
  - Contains deterministic business logic, including feature extraction and pattern detection.
  - Independent of frameworks and external systems.

- **Data Access Layer (`app/db/`)**
  - Manages persistence, queries, and schema definitions.

- **Authentication Layer (`app/auth/`)**
  - Handles JWT validation and tenancy enforcement.

- **Evaluation Layer (`eval/`)**
  - Provides reproducible evaluation pipelines and metrics computation.

This structure ensures that domain logic remains decoupled from infrastructure and framework-specific implementations.

---

## 2. Storage and Memory Model

### 2.1 Persistent Storage

The system uses **PostgreSQL** as the primary datastore.

- Ensures durability across container restarts.
- Supports structured queries required for behavioral analysis.
- Enables reliable storage of session summaries and detected patterns.

### 2.2 Structured Memory Representation

Session data is stored as **structured summaries** rather than unstructured text.

Each stored session includes:
- Summary text
- Behavioral metrics
- Tags
- References to raw session and trade data

This enables:
- Deterministic retrieval
- Query-based reasoning
- Traceability of all generated insights

---

## 3. Detection Engine Design

### 3.1 Deterministic Pattern Detection

Behavioral analysis is implemented using **rule-based feature engineering**.

Key characteristics:
- No LLM involvement in classification
- Fully deterministic outputs
- Direct mapping between input data and detected patterns

Examples of computed features:
- Trade frequency
- Time between trades
- Emotional state transitions
- Plan adherence scores
- Loss sequences

### 3.2 Evidence-Based Outputs

All detected behavioral patterns include explicit references:
- `sessionId`
- `tradeId`

This ensures:
- Verifiability of every claim
- Elimination of unsupported or inferred statements
- Compatibility with audit mechanisms

### 3.3 LLM Usage Scope

LLMs are restricted to:
- Formatting responses
- Generating coaching tone

LLMs are not used for:
- Behavioral classification
- Pattern detection
- Evidence generation

---

## 4. Security and Multi-Tenancy

### 4.1 JWT Authentication

The system uses **HS256 JWT tokens** for authentication.

Each request must:
- Include a valid token
- Pass signature verification
- Respect expiration constraints

### 4.2 Row-Level Tenancy Enforcement

Strict isolation is enforced using the `sub` claim in JWT:

```text
if jwt.sub != requestedUserId → HTTP 403
