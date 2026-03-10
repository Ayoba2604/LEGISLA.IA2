# Migracao do Projeto Atual

## Mantido

- Bloco PHP em `public/`, `routes/`, `app/controllers/` e `app/models/` para navegacao, sessao e login.
- JSONs em `IA/data/` como fixtures de demonstracao e smoke tests.

## Removido ou substituido

- Backend monolitico antigo em `IA/main.py`, agora substituido por um wrapper para `backend.app.main`.
- Chave Groq hardcoded removida de `IA/services/groq_client.py`.
- Cliente do chat nao depende mais de IP fixo.

## Criado

- Nova base modular em `backend/`.
- `migrations/`, `docker/`, `docs/`, `scripts/`.
- Runtime de fase 2 com LLM real opcional, retrieval via PostgreSQL/pgvector e ingestao por manifesto.

## Migracao de dados

1. Valide os seeds legados:

```bash
python -B scripts/migrate_legacy_data.py
```

2. Monte `backend/data/bootstrap/corpus_manifest.json` a partir de fontes oficiais/licenciadas.
3. Importe o corpus:

```bash
python -B scripts/import_corpus_manifest.py
```
