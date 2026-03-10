# LEGISLA.IA2

Refatoracao da IA juridica brasileira para uma base modular de producao com:

- FastAPI
- RAG hibrido com busca lexical + vetorial
- PostgreSQL + pgvector no runtime quando configurado
- tool calling juridico com LangChain
- fluxo pronto para LangGraph via `create_agent`
- reranker dedicado com fallback heuristico
- token assinado entre PHP e backend para sessao autenticada
- segregacao e retencao de documentos do usuario
- ingestao incremental por manifesto com trilha de jobs
- manutencao operacional com sync recorrente, limpeza de retencao e auditoria admin
- respostas estruturadas com fontes, limites e confianca
- pipeline de ingestao para uploads e corpus oficial/licenciado
- guardrails, rate limiting e trilha persistida de auditoria

## Estrutura principal

- `backend/`: novo backend Python de producao
- `docs/`: arquitetura, setup, API, migracao e avaliacao
- `migrations/`: Alembic + SQL
- `scripts/`: benchmark, ingestao, importacao de corpus e avaliacao
- `IA/`: camada de compatibilidade com o backend antigo
- `public/`, `app/`, `routes/`: camada PHP legada preservada

## Subida rapida

```bash
cp .env.example .env
docker compose up --build
```

## Backend local

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

## Importar corpus oficial/licenciado

1. Copie `backend/data/bootstrap/corpus_manifest.example.json` para `backend/data/bootstrap/corpus_manifest.json`.
2. Ajuste os caminhos locais e URLs oficiais/licenciadas.
3. Rode:

```bash
python -B scripts/import_corpus_manifest.py
```

## Avaliar

```bash
python -B scripts/run_benchmark.py
python -B scripts/run_legal_eval.py
```

## Operacao e manutencao

```bash
python -B scripts/run_maintenance.py --cleanup-expired-uploads
python -B scripts/run_maintenance.py --sync-manifest
```

## Documentacao

- [Arquitetura](docs/architecture.md)
- [Setup](docs/setup.md)
- [API](docs/api.md)
- [Migracao](docs/migration.md)
- [Avaliacao](docs/evaluation.md)
- [Checklist de producao](docs/production-checklist.md)
