
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Unified Trades Table (Canonical Schema)
CREATE TABLE IF NOT EXISTS trades (
    id                 UUID PRIMARY KEY, -- tradeId
    user_id            UUID NOT NULL,
    session_id         UUID NOT NULL,
    asset              TEXT NOT NULL,
    asset_class        TEXT NOT NULL, -- equity, crypto, forex
    direction          TEXT NOT NULL, -- long, short
    entry_price        NUMERIC(18,8) NOT NULL,
    exit_price         NUMERIC(18,8),
    quantity           NUMERIC(18,8) NOT NULL,
    entry_at           TIMESTAMPTZ NOT NULL,
    exit_at            TIMESTAMPTZ,
    status             TEXT NOT NULL, -- open, closed, cancelled
    plan_adherence     INTEGER CHECK (plan_adherence >= 1 AND plan_adherence <= 5),
    emotional_state    TEXT, -- calm, anxious, greedy, fearful, neutral
    entry_rationale    TEXT,
    
    -- AI/Computed Fields
    outcome            TEXT, -- win, loss
    pnl                NUMERIC(18,8),
    revenge_flag       BOOLEAN DEFAULT FALSE,
    
    created_at         TIMESTAMPTZ DEFAULT now(),
    updated_at         TIMESTAMPTZ DEFAULT now()
);

-- Session Summaries (Canonical Schema)
CREATE TABLE IF NOT EXISTS session_summaries (
    session_id         UUID PRIMARY KEY,
    user_id            UUID NOT NULL,
    date               TIMESTAMPTZ DEFAULT now(),
    notes              TEXT,
    trade_count        INTEGER DEFAULT 0,
    win_rate           FLOAT DEFAULT 0.0,
    total_pnl          NUMERIC(18,8) DEFAULT 0.0,
    embedding          vector(1536),
    created_at         TIMESTAMPTZ DEFAULT now()
);

-- Behavioral Pathologies (Memory Layer)
CREATE TABLE IF NOT EXISTS detected_patterns (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id            UUID NOT NULL,
    pattern_id         TEXT NOT NULL,
    session_ids        UUID[] NOT NULL DEFAULT '{}',
    trade_ids          UUID[] NOT NULL DEFAULT '{}',
    confidence         FLOAT NOT NULL,
    created_at         TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_trades_session ON trades(session_id);
CREATE INDEX IF NOT EXISTS idx_ss_user         ON session_summaries(user_id);
CREATE INDEX IF NOT EXISTS idx_dp_user         ON detected_patterns(user_id);