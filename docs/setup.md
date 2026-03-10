# Setup Local

## Requisitos

- Python 3.11+
- Docker e Docker Compose
- PostgreSQL 16 com extensao `pgvector` para ambiente de producao

## Subida rapida com Docker

```bash
cp .env.example .env
docker compose up --build
```

Servicos:

- PHP/web: `http://localhost:8080`
- Backend FastAPI: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

## Rodando backend localmente

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

## Variaveis relevantes da fase 4

- `LEGISLA_INTERNAL_SECRET`: segredo compartilhado entre PHP e backend para assinar o token de sessao.
- `REQUIRE_CHAT_AUTH=true`: exige autenticacao para todas as consultas do chat.
- `USER_UPLOAD_RETENTION_DAYS=30`: define retencao de uploads do usuario.
- `USE_LANGGRAPH_AGENT=true`: habilita o agente LangChain/LangGraph quando houver provider real.
- `RETRIEVAL_BACKEND=auto`: usa PostgreSQL/pgvector quando o banco estiver disponivel e cai para memoria no fallback.
- `RERANKER_PROVIDER=cross_encoder`: ativa reranker dedicado quando o modelo estiver instalado.
- `BOOTSTRAP_MANIFEST_PATH=backend/data/bootstrap/corpus_manifest.json`: manifesto de corpus oficial/licenciado.
- `ENABLE_LEGACY_BOOTSTRAP_FALLBACK=true`: preserva compatibilidade com os seeds antigos enquanto o corpus oficial nao estiver pronto.
- `MAINTENANCE_SCHEDULER_ENABLED=true`: liga o scheduler interno de sync e limpeza.
- `MAINTENANCE_AUTO_SYNC_ON_STARTUP=true`: dispara uma sincronizacao do manifesto ao subir a API.
- `MAINTENANCE_CLEANUP_INTERVAL_SECONDS=900`: periodicidade da limpeza de uploads expirados.
- `MAINTENANCE_SYNC_INTERVAL_SECONDS=3600`: periodicidade da sincronizacao do manifesto.
- `MAINTENANCE_CLEANUP_BATCH_SIZE=200`: lote maximo por limpeza.
- `LANGSMITH_TRACING=true`: habilita tracing externo do LangChain.

## Importar corpus oficial/licenciado

```bash
copy backend\\data\\bootstrap\\corpus_manifest.example.json backend\\data\\bootstrap\\corpus_manifest.json
python -B scripts/import_corpus_manifest.py
```

## Avaliar

```bash
python -B scripts/run_benchmark.py
python -B scripts/run_legal_eval.py
```

## Manutencao operacional

```bash
python -B scripts/run_maintenance.py --cleanup-expired-uploads
python -B scripts/run_maintenance.py --sync-manifest
python -B scripts/run_maintenance.py --sync-manifest --cleanup-expired-uploads
```

## Migracoes

```bash
alembic upgrade head
```
