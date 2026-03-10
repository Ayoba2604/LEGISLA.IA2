# Arquitetura Proposta

## Camadas

- `backend/app/api`: camada HTTP em FastAPI, incluindo aliases legados como `/perguntar`.
- `backend/app/services`: orquestracao do fluxo juridico, RAG, reranking e geracao de resposta.
- `backend/app/agents`: agente heuristico e runner LangChain/LangGraph para tool calling.
- `backend/app/ingestion`: ingestao de uploads, manifesto de corpus, sincronizacao incremental e normalizacao.
- `backend/app/retrievers`: busca hibrida, diversidade via MMR e reranking.
- `backend/app/security`: guardrails, validacao de upload, rate limit e autenticacao de rotas sensiveis.
- `backend/app/db`: modelos de persistencia, trilha de jobs e estado de sincronizacao.
- `backend/app/observability`: metricas, tracing por etapa e logs estruturados.

## Runtime da fase 3

- `ChatService` escolhe entre agente heuristico e agente LangChain conforme `USE_LANGGRAPH_AGENT` e provider disponivel.
- `LegalLLMService` usa modelo real via LangChain quando houver chave configurada e cai para resposta deterministica no fallback.
- `RetrievalService` usa PostgreSQL + pgvector quando `RETRIEVAL_BACKEND` estiver em `auto` ou `db` e o banco estiver disponivel.
- `RerankerService` aplica reranking dedicado por `cross_encoder` quando configurado, com fallback heuristico.
- `SourceCatalog` carrega primeiro um manifesto de corpus oficial/licenciado; se ele nao existir, pode cair para os seeds legados por compatibilidade.
- O PHP assina um token curto de sessao e o frontend o repassa ao backend em `X-Legisla-User-Token`.

## Runtime da fase 4

- `MaintenanceService` executa sincronizacao manual/automatizada do manifesto e limpeza de uploads expirados.
- `MaintenanceScheduler` pode rodar dentro da API, controlado por `MAINTENANCE_SCHEDULER_ENABLED`, sem alterar o fluxo HTTP existente.
- As rotas `/api/v1/admin/*` expõem auditoria operacional: jobs de ingestao, estados de sync, retrieval logs mascarados e uploads.
- `/health` agora informa se o banco responde, se `pgvector` esta disponivel e se ha pendencias operacionais de sync ou retencao.

## Estrategia de compatibilidade

- O legado PHP permanece como camada web e autenticacao.
- `IA/main.py` continua como entrypoint de compatibilidade para o backend novo.
- O chat segue acessivel pela pagina atual, mas agora envia token de sessao, segrega documentos do usuario e usa o endpoint `/api/v1/chat/query`.
