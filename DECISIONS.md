# Architectural Decisions & Design Patterns

Hey team, 

This document outlines the core architectural patterns and design decisions we've adopted for the Trading Psychology Coach. The goal here isn't just to build an app, but to build a robust, reproducible, and verifiable system that provides stateful coaching while strictly avoiding LLM hallucinations. Here's a breakdown of how we've structured the system and *why*.

## Layered Backend Architecture

We've opted for a strictly **Layered Architecture** to keep the separation of concerns crystal clear. If you look at the codebase, you'll see:
- `api/`: Our presentation layer. Just HTTP routes, request validation, and response serialization.
- `services/`: The orchestration layer. This ties together our business logic, database calls, and core engines.
- `core/`: The heart of the system. This holds pure, deterministic business logic.
- `db/`: The data access layer, handling persistent storage and query logic.
- `auth/`: Centralized authentication and authorization.
- `eval/`: Offline evaluation scripts and harnesses.

This modularity ensures that our core domain logic remains isolated from the specific web framework (FastAPI) or database driver we're using.

## Storage and Memory Model

### Relational Persistence (PostgreSQL)
For persistence, we went with **PostgreSQL**. The coaching memory has to survive container restarts, ruling out simple in-memory stores. Moreover, because we need to run complex, structured queries across historical trades, sessions, and detected patterns, a robust relational database is the right tool for the job.

### Structured Memory Summaries
Instead of letting an LLM blindly summarize past sessions into a raw text blob, we use a **Structured Memory Model**. We store sessions as structured summaries, complete with computed metrics, tags, and references to the exact raw session records. This structure is critical for exact retrieval and allows us to definitively point to *why* a particular coaching message was generated.

## The Detection Engine: Deterministic over Generative

When it comes to analyzing user behavior, we made a hard rule: **LLMs do not diagnose**. 

### Rule-Based Pattern Detection
We employ **Deterministic Pattern Detection** using rule-based feature engineering to identify behavioral pathologies. By calculating concrete features (like revenge trade counts, emotional instability, rapid re-entries, and average plan adherence) directly from raw trade data, we ensure our diagnostics are reproducible, auditable, and easily evaluable against ground truth.

### Evidence-Backed Claims
Every behavioral claim the system makes must provide receipts. It must include both a `sessionId` and a `tradeId`. This completely eliminates generic advice and hallucinated claims; every insight is traceable back to the source data. The LLM is strictly relegated to the presentation layer—it's meant to handle the wording, empathy, and coaching tone, but the actual reasoning comes from our deterministic `core/` engine.

## Security & Isolation

### JWT-based Multi-Tenancy Architecture
We are using JWT authentication (HS256) to ensure strict tenant isolation. Because this system deals with sensitive financial and psychological data, our golden rule is: `if jwt.sub !== requestedUserId`, it returns an immediate HTTP `403 Forbidden`. 
We've also standardized our error responses to ensure security audits always see standard codes (`401` for bad tokens, `403` for cross-tenant access).

## Operational & API Patterns

### The Anti-Hallucination Audit Pattern
We've introduced a dedicated `/audit` endpoint as a safety net. This allows external reviewers to programmatically verify that any referenced session IDs in the coaching messages actually exist in the database. It's a clean separation between the generation of insights and their verification.

### Server-Sent Events (SSE) for Streaming
To ensure a snappy user experience and fast initial response times, we are utilizing **Server-Sent Events (SSE)**. It's a perfect architectural fit for streaming token-by-token coaching messages one-way from the server to the client without the overhead of WebSockets.

## Reproducibility & Deployment

We treat the seed dataset (`nevup_seed_dataset.json`) as strictly read-only to guarantee consistent evaluation results. For the reproducible evaluation harness, we have a deterministic pipeline that loads data, computes features, detects patterns, aggregates predictions, and generates F1 scores cleanly.

On the dev-ops side:
- **Dependency Management:** We're standardizing on `uv` for blazing fast, lockfile-based installs.
- **Containerization:** We rely on Docker Compose to spin up the entire API, evaluation harness, and PostgreSQL database synchronously, without any manual setup steps required.

---

### In Summary

Our guiding principle is simple: **All behavioral claims must be grounded in stored evidence.** 
No invented sessions. No hallucinated trades. No unsupported psychology. We are building a system that is as explainable and reproducible as it is intelligent.