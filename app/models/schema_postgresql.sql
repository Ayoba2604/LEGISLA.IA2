-- PostgreSQL schema for LEGISLA.IA
-- Use with: psql -U postgres -f app/models/schema_postgresql.sql

-- 1) Database (optional if already exists)
CREATE DATABASE "UsuariosLegislaIA";

-- Connect to the database before running the rest:
-- \c "UsuariosLegislaIA"

-- 2) Main table used by UsuarioModel
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario BIGSERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL,
    admin BOOLEAN NOT NULL DEFAULT FALSE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- 3) Optional test seed
-- Password below is bcrypt for: admin123
INSERT INTO usuarios (nome, email, senha, admin)
VALUES (
    'Administrador',
    'admin@legislaia.local',
    '$2y$10$wH5i0Rr8Al2I7xw6Wn.mI.8u7wqjJmS5kVt8nP8qA3rN2YkN0JQ9K',
    TRUE
)
ON CONFLICT (email) DO NOTHING;
