# Checklist de Producao

- [ ] Configurar `LEGISLA_ADMIN_TOKEN`
- [ ] Configurar `LEGISLA_INTERNAL_SECRET` com o mesmo valor no PHP e no backend
- [ ] Definir `REQUIRE_CHAT_AUTH=true` se o chat nao puder ser anonimo
- [ ] Remover `LLM_PROVIDER=mock`
- [ ] Definir `RERANKER_PROVIDER=cross_encoder` se quiser reranker dedicado
- [ ] Apontar `DATABASE_URL` para PostgreSQL com `pgvector`
- [ ] Rodar `alembic upgrade head`
- [ ] Configurar origens CORS reais
- [ ] Decidir se o scheduler interno sera usado (`MAINTENANCE_SCHEDULER_ENABLED=true`) ou se a manutencao rodara via cron/CI
- [ ] Ativar coleta de logs, metricas e tracing externos
- [ ] Carregar corpus oficial de legislacao e jurisprudencia
- [ ] Validar politica de retencao de uploads e PII (`USER_UPLOAD_RETENTION_DAYS`)
- [ ] Rodar `python -B scripts/import_corpus_manifest.py`
- [ ] Rodar `python -B scripts/run_maintenance.py --cleanup-expired-uploads`
- [ ] Verificar `/api/v1/admin/overview` e `/health` apos subir o ambiente
- [ ] Rodar `python -B scripts/run_benchmark.py`
- [ ] Rodar `python -B scripts/run_legal_eval.py`
- [ ] Revisar limites, fallback e autenticacao antes de producao
