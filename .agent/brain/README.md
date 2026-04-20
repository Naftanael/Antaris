# Antaris Brain

Infraestrutura local de indexacao e recuperacao de contexto do projeto Antaris.

Componentes:
- `schema.sql`: schema SQLite/FTS5 do brain
- `brain_db.py`: contrato comum de acesso ao banco e utilitarios
- `ingest.py`: ingestao incremental de notas, memoria, manifest e skills
- `embeddings.py`: geracao incremental de embeddings locais
- `search.py`: busca lexical, semantica e hibrida
- `watcher.py`: observacao de mudancas e reindexacao automatica
- `decay.py`: manutencao semanal de relevance_score
- `stats.py`: dashboard de saude do brain

Uso rapido:

```bash
cd .agent/brain
.venv/bin/python ingest.py
.venv/bin/python embeddings.py --limit 200
.venv/bin/python search.py query "persona arquiteto" --limit 5 --mode hybrid
.venv/bin/python stats.py
```

Observacoes:
- a venv local do brain nao e versionada
- `brain.db` e um artefato local de runtime
- o sistema usa SQLite FTS5 + embeddings locais para reduzir custo de contexto
