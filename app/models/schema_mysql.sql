-- MySQL schema for LEGISLA.IA
-- Use with: mysql -u root -p < app/models/schema_mysql.sql

CREATE DATABASE IF NOT EXISTS UsuariosLegislaIA
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE UsuariosLegislaIA;

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL,
    senha VARCHAR(255) NOT NULL,
    admin TINYINT(1) NOT NULL DEFAULT 0,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_usuario),
    UNIQUE KEY uq_usuarios_email (email)
) ENGINE=InnoDB;

-- Password below is bcrypt for: admin123
INSERT IGNORE INTO usuarios (nome, email, senha, admin)
VALUES (
    'Administrador',
    'admin@legislaia.local',
    '$2y$10$wH5i0Rr8Al2I7xw6Wn.mI.8u7wqjJmS5kVt8nP8qA3rN2YkN0JQ9K',
    1
);
