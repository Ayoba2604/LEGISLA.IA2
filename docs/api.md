# Rotas Principais

## Runtime

- `GET /health`
- `GET /api/v1/health`
- `POST /api/v1/chat/query`
- `POST /api/v1/ingestion/upload`
- `POST /api/v1/ingestion/manifest`
- `POST /api/v1/ingestion/legacy-migration`

## Admin / Operacao

- `GET /api/v1/admin/overview`
- `GET /api/v1/admin/metrics`
- `GET /api/v1/admin/retrieval-logs`
- `GET /api/v1/admin/ingestion/jobs`
- `GET /api/v1/admin/ingestion/sync-state`
- `GET /api/v1/admin/uploads`
- `POST /api/v1/admin/maintenance/cleanup-uploads`
- `POST /api/v1/admin/maintenance/sync-manifest`

## Compatibilidade legada

- `POST /perguntar`
- `GET /consulta`
- `POST /resumir_pdf`
- `POST /resumir_video`
- `GET /public/index.php?route=consultas/chat-token`

## Headers relevantes

- `X-Admin-Token`: exigido pelas rotas admin e pelas rotas de ingestao sensiveis
- `X-Legisla-User-Token`: token assinado pelo PHP para upload e segregacao de documentos do usuario

## Exemplo de consulta

```json
POST /api/v1/chat/query
{
  "question": "Quais sao meus direitos em uma compra com defeito?",
  "mode": "friendly",
  "user_document_ids": [],
  "debug": true
}
```

## Exemplo de importacao de manifesto

```json
POST /api/v1/ingestion/manifest
{
  "manifest_path": "backend/data/bootstrap/corpus_manifest.json",
  "persist": true,
  "source_types": ["legislation", "jurisprudence"]
}
```

## Exemplo de limpeza de uploads expirados

```json
POST /api/v1/admin/maintenance/cleanup-uploads
{
  "limit": 200,
  "hard_delete": false
}
```
