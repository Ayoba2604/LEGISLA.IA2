CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS sources (
    id VARCHAR(64) PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,
    authority VARCHAR(20) NOT NULL,
    is_official BOOLEAN NOT NULL DEFAULT FALSE,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    url_origem VARCHAR(1000),
    hash_documento VARCHAR(128),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sources_type ON sources (source_type);
CREATE INDEX IF NOT EXISTS idx_sources_official ON sources (is_official);

CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(64) PRIMARY KEY,
    source_id VARCHAR(64) NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    canonical_title VARCHAR(500) NOT NULL,
    language VARCHAR(10) NOT NULL DEFAULT 'pt-BR',
    current_version_id VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS document_versions (
    id VARCHAR(64) PRIMARY KEY,
    document_id VARCHAR(64) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_label VARCHAR(50) NOT NULL,
    hash_documento VARCHAR(128) NOT NULL,
    raw_text TEXT NOT NULL,
    vigente BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_document_version_label UNIQUE (document_id, version_label)
);

CREATE TABLE IF NOT EXISTS chunks (
    id VARCHAR(64) PRIMARY KEY,
    source_id VARCHAR(64) NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    document_id VARCHAR(64) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_id VARCHAR(64) NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    search_vector_text TEXT NOT NULL,
    hierarchy JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks (document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_version ON chunks (version_id);
CREATE INDEX IF NOT EXISTS idx_chunks_fts ON chunks USING gin (to_tsvector('portuguese', search_vector_text));

CREATE TABLE IF NOT EXISTS embeddings (
    id BIGSERIAL PRIMARY KEY,
    chunk_id VARCHAR(64) NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    model_name VARCHAR(120) NOT NULL,
    version_label VARCHAR(50) NOT NULL,
    embedding vector(256) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_chunk ON embeddings (chunk_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings (model_name, version_label);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(64) PRIMARY KEY,
    channel VARCHAR(50) NOT NULL DEFAULT 'web',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(64) PRIMARY KEY,
    conversation_id VARCHAR(64) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0,
    cost_usd DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages (conversation_id, created_at);

CREATE TABLE IF NOT EXISTS citations (
    id VARCHAR(64) PRIMARY KEY,
    conversation_id VARCHAR(64) REFERENCES conversations(id) ON DELETE SET NULL,
    message_id VARCHAR(64) REFERENCES messages(id) ON DELETE SET NULL,
    chunk_id VARCHAR(64) NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    source_id VARCHAR(64) NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    reference_label VARCHAR(500) NOT NULL,
    quote TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS retrieval_logs (
    id BIGSERIAL PRIMARY KEY,
    conversation_id VARCHAR(64) REFERENCES conversations(id) ON DELETE SET NULL,
    query_text TEXT NOT NULL,
    intent VARCHAR(50),
    filters JSONB NOT NULL DEFAULT '{}'::jsonb,
    selected_chunk_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    latency_ms DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_retrieval_logs_intent ON retrieval_logs (intent);

CREATE TABLE IF NOT EXISTS user_uploads (
    id VARCHAR(64) PRIMARY KEY,
    conversation_id VARCHAR(64) REFERENCES conversations(id) ON DELETE SET NULL,
    filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(120) NOT NULL,
    file_size INTEGER NOT NULL,
    storage_path VARCHAR(500),
    source_id VARCHAR(64) REFERENCES sources(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_uploads_source ON user_uploads (source_id);

CREATE TABLE IF NOT EXISTS legal_entities (
    id BIGSERIAL PRIMARY KEY,
    source_id VARCHAR(64) NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_value VARCHAR(255) NOT NULL,
    normalized_value VARCHAR(255) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_legal_entities_lookup ON legal_entities (entity_type, normalized_value);

CREATE TABLE IF NOT EXISTS jurisprudence_metadata (
    source_id VARCHAR(64) PRIMARY KEY REFERENCES sources(id) ON DELETE CASCADE,
    tribunal VARCHAR(120),
    orgao_julgador VARCHAR(120),
    numero_processo VARCHAR(120),
    relator VARCHAR(120),
    data_julgamento TIMESTAMPTZ,
    data_publicacao TIMESTAMPTZ,
    ementa TEXT,
    tese TEXT
);

CREATE INDEX IF NOT EXISTS idx_juris_tribunal ON jurisprudence_metadata (tribunal);
CREATE INDEX IF NOT EXISTS idx_juris_processo ON jurisprudence_metadata (numero_processo);

CREATE TABLE IF NOT EXISTS legislation_metadata (
    source_id VARCHAR(64) PRIMARY KEY REFERENCES sources(id) ON DELETE CASCADE,
    numero_norma VARCHAR(120),
    tipo_norma VARCHAR(50),
    artigo VARCHAR(50),
    vigencia VARCHAR(120),
    data_publicacao DATE,
    uf VARCHAR(2)
);

CREATE INDEX IF NOT EXISTS idx_legislation_norma ON legislation_metadata (numero_norma);
CREATE INDEX IF NOT EXISTS idx_legislation_artigo ON legislation_metadata (artigo);

CREATE TABLE IF NOT EXISTS contracts_metadata (
    source_id VARCHAR(64) PRIMARY KEY REFERENCES sources(id) ON DELETE CASCADE,
    contract_type VARCHAR(120),
    parties_count INTEGER,
    contains_personal_data BOOLEAN NOT NULL DEFAULT FALSE,
    contains_arbitration_clause BOOLEAN NOT NULL DEFAULT FALSE
);
