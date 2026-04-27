
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS session_summaries (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     TEXT NOT NULL,
    session_id  TEXT NOT NULL UNIQUE,
    summary     TEXT NOT NULL,
    metrics     JSONB NOT NULL,
    tags        TEXT[] NOT NULL DEFAULT '{}',
    raw_trades  JSONB NOT NULL DEFAULT '[]',
    embedding   vector(1536),
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS detected_patterns (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id      TEXT NOT NULL,
    pattern_id   TEXT NOT NULL,
    session_ids  TEXT[] NOT NULL DEFAULT '{}',
    trade_ids    TEXT[] NOT NULL DEFAULT '{}',
    confidence   FLOAT NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ss_user    ON session_summaries(user_id);
CREATE INDEX IF NOT EXISTS idx_ss_sid     ON session_summaries(session_id);
CREATE INDEX IF NOT EXISTS idx_dp_user    ON detected_patterns(user_id);