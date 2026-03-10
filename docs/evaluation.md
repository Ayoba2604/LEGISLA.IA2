# Avaliacao

## Benchmark legado

O benchmark inicial continua em `backend/data/bootstrap/evaluation_dataset.json` e e executado por:

```bash
python -B scripts/run_benchmark.py
```

## Avaliacao expandida da fase 3

O dataset da fase 3 esta em `backend/data/evaluation/legal_eval_dataset.json` e cobre:

- artigo exato
- pergunta conceitual
- divergencia jurisprudencial
- norma revogada
- clausula abusiva
- conflito entre documento do usuario e legislacao
- ausencia de base suficiente
- prompt injection em documento

Execute com:

```bash
python -B scripts/run_legal_eval.py
```

O script monta um corpus sintetico controlado e mede a aderencia por check esperado.
