---
tipo: proposta-arquitetura
status: draft
autor: Claude (Hermes Agent)
criado: 2026-04-20
versao: 1.0
tags: [indexacao, rag, memoria, agente, sqlite, fts5, embeddings]
---

# Proposta: Sistema Autonomo de Indexacao de Dados para o Agente

## Contexto e Problema

O que temos hoje (2026-04-20):
- `.agent/vault-index.json` -- indice estatico, regenerado inteiro a cada checkpoint
- `.agent/memory/*.md` -- memoria persistente escrita pelo agente
- `obsidian_search.py` -- busca lexical simples por score somado

Limitacoes:
1. **Sem semantica**: busca por "reduzir gastos em LLM" nao acha uma nota chamada "LLM Optimization Engine" se a palavra "reduzir" nao aparecer
2. **Nao incremental**: regenerar o indice inteiro e O(N). Escalona mal se passar de 1000 notas
3. **Memoria nao indexada**: o agente escreve em session-log.md mas nao consegue buscar rapido em sessoes passadas
4. **Sem telemetria**: nao sei o que o agente acessa mais, o que e util, o que e ruido
5. **Sem deduplicacao**: uma mesma informacao pode estar em 3 lugares sem eu notar

## Objetivo

Sistema autonomo que:
- Indexa automaticamente tudo que e relevante (notas, memoria, transcripts de sessao, interacoes com o agente)
- Busca e **rapida** (< 50ms para queries lexicais, < 200ms para semanticas)
- Se mantem atualizado **incrementalmente** (so indexa o que mudou)
- Aprende com o uso: notas mais acessadas ganham boost, nao-usadas decaem
- Roda autonomo (watcher + cron) sem eu pedir

## Arquitetura Proposta

### Stack tecnologica

Tudo local, zero dependencias externas, zero custos:

| Camada | Tecnologia | Justificativa |
|---|---|---|
| Storage | SQLite 3.45 (ja instalado) | Um arquivo, ACID, embedado, backup trivial |
| Full-text | FTS5 (nativo do SQLite) | Ranking BM25, stemming PT-BR, tokenizer unicode |
| Embeddings | sentence-transformers (opcional, fase 2) | Modelo pequeno (22MB) roda em CPU, ~50ms/doc |
| Vetores | sqlite-vec (extensao) OU numpy (fallback) | KNN eficiente dentro do mesmo .db |
| Scheduler | cron do sistema + hermes cronjob | Ja temos cronjob no Hermes |
| Watcher | inotifywait (nativo Linux) | Detecta mudanca em arquivo em tempo real |

### Esquema do banco (`.agent/brain.db`)

```sql
-- Tabela principal: documentos indexaveis (notas + entradas de memoria + transcripts)
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,        -- 'note', 'memory', 'session', 'skill'
    source_path TEXT NOT NULL,         -- path relativo ou id logico
    title TEXT,
    content TEXT NOT NULL,
    tags TEXT,                         -- JSON array
    frontmatter TEXT,                  -- JSON do YAML
    content_hash TEXT NOT NULL,        -- sha1 -- detecta mudanca sem reparse
    size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    relevance_score REAL DEFAULT 1.0,  -- boost ajustado por uso
    UNIQUE(source_type, source_path)
);

-- FTS5 virtual table (full-text search)
CREATE VIRTUAL TABLE documents_fts USING fts5(
    title, content, tags,
    content='documents',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'  -- trata acentos PT-BR
);

-- Triggers para manter FTS sincronizado
CREATE TRIGGER documents_ai AFTER INSERT ON documents BEGIN
    INSERT INTO documents_fts(rowid, title, content, tags)
    VALUES (new.id, new.title, new.content, new.tags);
END;
-- (analog para UPDATE e DELETE)

-- Chunks (para notas longas: RAG)
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    embedding BLOB  -- vetor serializado (fase 2)
);

CREATE VIRTUAL TABLE chunks_fts USING fts5(
    content, content='chunks', content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);

-- Links entre documentos (grafo)
CREATE TABLE links (
    from_id INTEGER REFERENCES documents(id),
    to_id INTEGER REFERENCES documents(id),
    link_type TEXT,  -- 'wikilink', 'tag_peer', 'backlink'
    weight REAL DEFAULT 1.0,
    PRIMARY KEY (from_id, to_id, link_type)
);

-- Telemetria: o que o agente busca/acessa
CREATE TABLE access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER REFERENCES documents(id),
    query TEXT,
    context TEXT,  -- 'search' | 'read' | 'related'
    session_id TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices
CREATE INDEX idx_doc_updated ON documents(updated_at DESC);
CREATE INDEX idx_doc_source ON documents(source_type, source_path);
CREATE INDEX idx_doc_hash ON documents(content_hash);
CREATE INDEX idx_log_time ON access_log(timestamp DESC);
CREATE INDEX idx_links_from ON links(from_id);
CREATE INDEX idx_links_to ON links(to_id);
```

### Por que SQLite FTS5 e a melhor escolha

Comparei as opcoes comuns:

| Opcao | Throughput | Latencia | Setup | Disco | Semantica |
|---|---|---|---|---|---|
| grep / ripgrep | alto | ~500ms em 10k arquivos | zero | zero | nao |
| ElasticSearch | alto | ~20ms | pesado (JVM, servico) | GB | plugin |
| Meilisearch | alto | ~10ms | servico | MB | plugin |
| Weaviate/Chroma | medio | ~100ms | servico + modelo | GB | sim |
| **SQLite FTS5** | **alto** | **~5ms** | **zero** | **KB-MB** | **via extensao** |

FTS5 ganha porque:
1. Ja esta instalado (zero deps novas)
2. Latencia de 5ms para buscas lexicais em 10k docs (BM25 nativo)
3. Mesma transacao suporta FTS + metadados + links + telemetria
4. Backup = `cp brain.db brain.db.bak`
5. Extensao `sqlite-vec` adiciona semantica no mesmo arquivo

### Pipeline de ingestao

```
                     ┌─ manual: hermes command ─┐
                     │                           │
 fonte de dados ─────┼─ inotify watcher ────────┼──> ingestor.py ──> brain.db
                     │                           │         │
                     └─ cron (a cada 15 min) ────┘         ├─> parse frontmatter
                                                           ├─> split em chunks
                                                           ├─> calcula hash
                                                           ├─> skip se nao mudou
                                                           ├─> atualiza FTS
                                                           └─> atualiza links
```

Fontes que entram no indice:
1. **Notas do vault** (`*.md` exceto infra)
2. **Memoria do agente** (`.agent/memory/*.md`)
3. **Context manifest** (`.agent/context-manifest.md`)
4. **Skills carregadas** (resumos das skills em `~/.hermes/skills`)
5. **Transcripts de sessao** (se disponivel via session_search)
6. **Clipboard snapshots** (opcional, fase 3 -- so se voce quiser)

### Componentes e arquivos

```
.agent/
├── brain.db                          # o indice (SQLite)
├── brain/
│   ├── schema.sql                    # schema completo
│   ├── ingest.py                     # pipeline de indexacao
│   ├── search.py                     # interface de busca (hibrida)
│   ├── watcher.py                    # daemon inotify
│   ├── cron_reindex.py              # roda a cada 15 min, pega o que escapou
│   ├── decay.py                      # decay de relevance_score semanal
│   ├── stats.py                      # telemetria, dashboard texto
│   └── embeddings.py                 # fase 2: sentence-transformers
├── memory/                           # (ja existe)
├── scripts/                          # (ja existe: obsidian_*.py)
└── context-manifest.md               # (ja existe)
```

Os scripts atuais (`obsidian_search.py`, `obsidian_recent.py`, `obsidian_related.py`) viram **facades** sobre `brain.db`. A API externa nao muda.

### API unificada: `search.py`

```python
# Busca hibrida: FTS + (opcional) embeddings + boost por relevance_score
search.query("como reduzir tokens em LLM", mode="hybrid", limit=5)
# Retorna: [(doc_id, title, snippet, score, source_type)]

# Busca por similaridade (embeddings, fase 2)
search.similar_to(doc_id, limit=5)

# Busca em uma dimensao so
search.fts("persona arquiteto")           # so FTS5
search.recent(days=7)                      # so por data
search.related(doc_id)                     # so grafo de links
search.top_accessed(days=30)               # top notas que o agente mais usou
```

### Autonomia: como o sistema "aprende"

1. **Telemetria de acesso**: toda query do agente e logada em `access_log`. Nota acessada -> `access_count++`, `last_accessed=now()`.

2. **Decay semanal** (`decay.py`, cron semanal):
   - Notas nao acessadas em 90 dias: `relevance_score *= 0.9`
   - Notas com backlinks: `relevance_score *= 1.1`
   - Notas atualizadas recentemente: `relevance_score *= 1.2`

3. **Boost em ranking**: `final_score = bm25_score * relevance_score`. Notas que voce usa sobem no ranking automaticamente.

4. **Detector de duplicatas**: chunks com similaridade > 0.95 disparam sugestao de merge (fase 2).

5. **Detector de orfas**: notas sem links_in nem tags sao listadas no briefing semanal pro agente sugerir conexoes.

### Performance esperada

Com 10.000 documentos (30x o vault atual):
- Ingest inicial: ~2 min
- Re-ingest incremental (1 nota mudou): ~10ms
- FTS query: 2-5ms
- Hybrid query (FTS + embedding): 80-150ms
- Tamanho do brain.db: ~50 MB (sem embeddings) ou ~200 MB (com embeddings)

Comparacao com abordagem atual:
- vault-index.json regeneracao: ~800ms para 29 notas, ~5min para 10k notas (nao escala)
- brain.db re-ingest: ~10ms por mudanca (escala linearmente por delta, nao por total)

### Economia de contexto

Quando eu (agente) preciso de informacao:

**Antes**:
1. Carrego vault-index.json inteiro (~4k tokens hoje, ~140k em escala)
2. Mesmo so pra responder "o que voce sabe sobre X"

**Depois**:
1. `search.py query "X" --limit 3`
2. Recebo 3 snippets de ~200 tokens cada = 600 tokens
3. Economia: 95%+ em escala

### Fases de implementacao

**Fase 1 (2h) - nucleo funcional**:
- [ ] schema.sql
- [ ] ingest.py (notas + memoria)
- [ ] search.py (FTS5 hibrido com boost por relevance_score)
- [ ] migracao: popular brain.db com tudo que ja existe
- [ ] obsidian_search.py vira facade sobre brain.db
- [ ] cron_reindex.py (hermes cronjob a cada 15 min)

**Fase 2 (2h) - semantica**:
- [ ] embeddings.py com sentence-transformers (modelo paraphrase-multilingual-MiniLM-L12-v2, 118MB, suporta PT-BR)
- [ ] sqlite-vec extension OU numpy cosine fallback
- [ ] chunking inteligente (por heading) para notas longas
- [ ] busca hibrida real (FTS score + embedding score, reciprocal rank fusion)

**Fase 3 (1h) - autonomia**:
- [ ] watcher.py (inotify, background process)
- [ ] decay.py (cron semanal)
- [ ] stats.py + dashboard em texto
- [ ] detector de orfas e duplicatas
- [ ] briefing semanal em `.agent/memory/briefing.md`

**Fase 4 (opcional) - expansao**:
- [ ] Ingestao de clipboard (se voce ativar)
- [ ] Ingestao de transcripts de sessao do Hermes
- [ ] Ingestao de emails (himalaya) / links salvos

### Metricas de sucesso

| Metrica | Baseline atual | Alvo pos-implementacao |
|---|---|---|
| Tokens por bootstrap | 2.4k | 2.4k (inalterado, manifest ainda e o core) |
| Tokens por query | N/A (lia nota inteira) | < 1k (3 snippets) |
| Latencia de busca | 800ms (regen) | < 10ms (FTS) |
| Recall semantico | baixo (so lexical) | alto (com embeddings) |
| Cobertura (docs indexados) | 29 | 29 + memoria + skills = ~50 |
| Autonomia | manual (regen no checkpoint) | auto (watcher + cron) |

## Decisoes que preciso de voce

1. **Sentence-transformers (118 MB)**: posso baixar o modelo? Baixa uma vez, usa sempre localmente. Ou prefere ficar so com FTS por enquanto (fase 1 apenas)?

2. **Autonomia do watcher**: posso rodar um daemon inotify em background? Custo: ~20 MB RAM, zero CPU quando nao ha mudanca. Alternativa: so cron a cada 15 min.

3. **Escopo de ingestao inicial**: comecar so com o vault (29 notas)? Ou incluir desde ja:
   - skills do Hermes (~60 skills em ~/.hermes/skills)
   - session logs antigos via session_search
   - Documentos/BarberFlow (codigo do projeto ativo)

4. **Implementar fase 1 agora, ou aprovar tudo e fazer sequencialmente?**

## Relacionado

- [[Proposta - Integracao Hermes x Obsidian]]
- [[LLM Optimization Engine]]
- [[Antaris-Architecture-For-AI]]
