-- ============================================================
-- Code-Swarm Database Schema (PostgreSQL 15+)
-- SOTA: pgvector for embeddings, UUID primary keys,
--        Row Level Security, JSONB for flexible data
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy search

-- Enums
CREATE TYPE agent_status AS ENUM ('idle', 'active', 'busy', 'error', 'offline');
CREATE TYPE task_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
CREATE TYPE event_type AS ENUM ('task', 'agent', 'system', 'feedback');

-- ============================================================
-- AGENTS
-- ============================================================
CREATE TABLE agents (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT NOT NULL UNIQUE,
    model       TEXT NOT NULL,
    fallback_model TEXT,
    role        TEXT NOT NULL,  -- planner, executor, validator, etc.
    status      agent_status DEFAULT 'idle',
    capabilities TEXT[] DEFAULT '{}',
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ,
    version     INTEGER DEFAULT 1
);

CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_role ON agents(role);
CREATE INDEX idx_agents_capabilities ON agents USING GIN(capabilities);

-- ============================================================
-- SESSIONS
-- ============================================================
CREATE TABLE sessions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    swarm_id    TEXT NOT NULL,
    user_id     TEXT,
    agent_id    UUID REFERENCES agents(id),
    status      TEXT DEFAULT 'active',
    context     JSONB DEFAULT '{}',
    started_at  TIMESTAMPTZ DEFAULT NOW(),
    ended_at    TIMESTAMPTZ,
    duration_ms INTEGER,
    error_count INTEGER DEFAULT 0,
    metrics     JSONB DEFAULT '{}'
);

CREATE INDEX idx_sessions_swarm ON sessions(swarm_id);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_started ON sessions(started_at DESC);

-- ============================================================
-- TASKS
-- ============================================================
CREATE TABLE tasks (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id  UUID REFERENCES sessions(id),
    title       TEXT NOT NULL,
    description TEXT,
    status      task_status DEFAULT 'pending',
    priority    INTEGER DEFAULT 5,
    assigned_to UUID REFERENCES agents(id),
    parent_id   UUID REFERENCES tasks(id),
    root_id     UUID REFERENCES tasks(id),  -- For task trees
    plan        JSONB,  -- Plan data from planning agent
    result      JSONB,
    error       TEXT,
    depends_on  UUID[] DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    started_at  TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    score       FLOAT,  -- Quality score from validation
    tags        TEXT[] DEFAULT '{}'
);

CREATE INDEX idx_tasks_session ON tasks(session_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority DESC);
CREATE INDEX idx_tasks_assigned ON tasks(assigned_to);
CREATE INDEX idx_tasks_root ON tasks(root_id);

-- ============================================================
-- MEMORY (Vector Embeddings via pgvector)
-- ============================================================
CREATE TABLE memory (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id    UUID REFERENCES agents(id),
    session_id  UUID REFERENCES sessions(id),
    task_id     UUID REFERENCES tasks(id),
    key         TEXT NOT NULL,
    value       TEXT NOT NULL,
    embedding   VECTOR(1536),  -- OpenAI ada-002 / text-embedding-3-small
    tags        TEXT[] DEFAULT '{}',
    importance  FLOAT DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    expires_at  TIMESTAMPTZ  -- Optional TTL
);

CREATE INDEX idx_memory_agent ON memory(agent_id);
CREATE INDEX idx_memory_key ON memory(key);
CREATE INDEX idx_memory_tags ON memory USING GIN(tags);
CREATE INDEX idx_memory_embedding ON memory USING IVFFlat(embedding vector_cosine_ops);

-- ============================================================
-- EVENTS (Append-only Event Log)
-- ============================================================
CREATE TABLE events (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id  UUID REFERENCES sessions(id),
    agent_id    UUID REFERENCES agents(id),
    type        event_type NOT NULL,
    action      TEXT NOT NULL,
    data        JSONB DEFAULT '{}',
    trace_id    TEXT,  -- For distributed tracing
    span_id     TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Create partitions by month (auto-create in production)
CREATE TABLE events_default PARTITION OF events DEFAULT;

CREATE INDEX idx_events_session ON events(session_id);
CREATE INDEX idx_events_agent ON events(agent_id);
CREATE INDEX idx_events_type ON events(type);
CREATE INDEX idx_events_trace ON events(trace_id);
CREATE INDEX idx_events_created ON events(created_at DESC);

-- ============================================================
-- FEEDBACK & LEARNING
-- ============================================================
CREATE TABLE feedback (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id     UUID REFERENCES tasks(id),
    agent_id    UUID REFERENCES agents(id),
    type        TEXT NOT NULL,  -- human, automated, peer
    rating      FLOAT,  -- 0-1 quality rating
    content     TEXT,
    tags        TEXT[] DEFAULT '{}',
    model_id    TEXT,  -- Which model produced the response
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_feedback_task ON feedback(task_id);
CREATE INDEX idx_feedback_agent ON feedback(agent_id);

-- ============================================================
-- SWARM STATE (Current swarm configuration snapshot)
-- ============================================================
CREATE TABLE swarm_state (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    swarm_id    TEXT NOT NULL UNIQUE,
    config      JSONB NOT NULL DEFAULT '{}',
    active_agents UUID[] DEFAULT '{}',
    health      JSONB DEFAULT '{}',
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ARTIFACTS (S3 references + metadata)
-- ============================================================
CREATE TABLE artifacts (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id  UUID REFERENCES sessions(id),
    task_id     UUID REFERENCES tasks(id),
    agent_id    UUID REFERENCES agents(id),
    name        TEXT NOT NULL,
    mime_type   TEXT,
    size_bytes  BIGINT,
    storage_path TEXT NOT NULL,  -- S3 key
    storage_bucket TEXT,
    checksum    TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_artifacts_session ON artifacts(session_id);
CREATE INDEX idx_artifacts_task ON artifacts(task_id);

-- ============================================================
-- Row Level Security (RLS) Policies
-- ============================================================
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

-- Policies: users can only see their own data (via user_id)
CREATE POLICY agents_user_policy ON agents
    FOR ALL USING (true);  -- Agents are public for now

CREATE POLICY sessions_user_policy ON sessions
    FOR ALL USING (true);  -- Adjust for multi-tenancy

CREATE POLICY tasks_user_policy ON tasks
    FOR ALL USING (true);

CREATE POLICY memory_user_policy ON memory
    FOR ALL USING (true);

CREATE POLICY events_user_policy ON events
    FOR ALL USING (true);

-- ============================================================
-- Triggers for updated_at
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER memory_updated_at BEFORE UPDATE ON memory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER swarm_state_updated_at BEFORE UPDATE ON swarm_state
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- View: Active Sessions with Agents
-- ============================================================
CREATE VIEW active_sessions AS
SELECT
    s.id,
    s.swarm_id,
    s.user_id,
    s.status,
    s.started_at,
    a.name AS agent_name,
    a.model,
    s.context,
    s.error_count,
    EXTRACT(EPOCH FROM (NOW() - s.started_at))::INTEGER AS duration_sec
FROM sessions s
LEFT JOIN agents a ON s.agent_id = a.id
WHERE s.status IN ('active', 'running');

-- ============================================================
-- View: Task Performance Metrics
-- ============================================================
CREATE VIEW task_metrics AS
SELECT
    DATE(completed_at) AS date,
    status,
    COUNT(*) AS task_count,
    AVG(duration_ms)::INTEGER AS avg_duration_ms,
    AVG(score) AS avg_score,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_ms) AS p50_duration,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_duration
FROM tasks
WHERE completed_at IS NOT NULL
GROUP BY DATE(completed_at), status
ORDER BY date DESC;

-- ============================================================
-- Function: Full-text search on memory
-- ============================================================
CREATE OR REPLACE FUNCTION search_memory(query TEXT, limit_n INTEGER DEFAULT 10)
RETURNS TABLE(id UUID, key TEXT, value TEXT, similarity FLOAT) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.id,
        m.key,
        m.value,
        1 - (m.value <=> query::TSVECTOR) AS similarity
    FROM memory m
    WHERE m.value ILIKE '%' || query || '%'
    ORDER BY similarity DESC
    LIMIT limit_n;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- Function: Agent health check
-- ============================================================
CREATE OR REPLACE FUNCTION agent_health(agent_uuid UUID)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    task_count INTEGER;
    error_count INTEGER;
    avg_score FLOAT;
BEGIN
    SELECT COUNT(*), SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), AVG(score)
    INTO task_count, error_count, avg_score
    FROM tasks
    WHERE assigned_to = agent_uuid
      AND created_at > NOW() - INTERVAL '1 hour';

    SELECT jsonb_build_object(
        'task_count', COALESCE(task_count, 0),
        'error_count', COALESCE(error_count, 0),
        'avg_score', COALESCE(avg_score, 0),
        'error_rate', CASE WHEN task_count > 0 THEN error_count::FLOAT / task_count ELSE 0 END
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE agents IS 'Agent registry with capabilities and status tracking';
COMMENT ON TABLE sessions IS 'Swarm sessions with context and metrics';
COMMENT ON TABLE tasks IS 'Task tree with dependency tracking and quality scoring';
COMMENT ON TABLE memory IS 'Persistent memory with vector embeddings for semantic search';
COMMENT ON TABLE events IS 'Append-only event log partitioned by time for audit trail';
COMMENT ON TABLE feedback IS 'RLHF feedback for self-improvement';
COMMENT ON TABLE artifacts IS 'S3 artifact references with metadata';