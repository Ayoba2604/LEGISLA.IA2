ALTER TABLE conversations
    ADD COLUMN IF NOT EXISTS owner_user_id VARCHAR(64);

CREATE INDEX IF NOT EXISTS idx_conversations_owner_user ON conversations (owner_user_id);

ALTER TABLE user_uploads
    ADD COLUMN IF NOT EXISTS owner_user_id VARCHAR(64),
    ADD COLUMN IF NOT EXISTS retention_expires_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_user_uploads_owner_user ON user_uploads (owner_user_id);
CREATE INDEX IF NOT EXISTS idx_user_uploads_retention ON user_uploads (retention_expires_at);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id BIGSERIAL PRIMARY KEY,
    manifest_path VARCHAR(500) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'running',
    source_types JSONB NOT NULL DEFAULT '[]'::jsonb,
    imported_sources INTEGER NOT NULL DEFAULT 0,
    imported_chunks INTEGER NOT NULL DEFAULT 0,
    skipped_sources INTEGER NOT NULL DEFAULT 0,
    failed_sources INTEGER NOT NULL DEFAULT 0,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status ON ingestion_jobs (status, created_at DESC);

CREATE TABLE IF NOT EXISTS source_sync_state (
    source_key VARCHAR(255) PRIMARY KEY,
    source_id VARCHAR(64),
    version_id VARCHAR(64),
    last_hash VARCHAR(128),
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    last_error TEXT,
    last_synced_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_source_sync_state_status ON source_sync_state (status, last_synced_at DESC);
