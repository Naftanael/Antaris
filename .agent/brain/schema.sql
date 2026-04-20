-- Schema do "cerebro" do agente
-- Arquivo: .agent/brain.db
-- Motor: SQLite 3.45+ com FTS5 e sqlite-vec (opcional)
--
-- Principios:
--   1. Uma unica fonte de verdade por documento (tabela `documents`)
--   2. FTS5 derivada via triggers (sempre consistente)
--   3. Chunks separados para notas longas (RAG)
--   4. Grafo de links explicito (queryavel)
--   5. Telemetria como cidada de primeira classe (melhora ranking)
--   6. Soft delete via `deleted_at` (permite auditoria)

PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;
PRAGMA temp_store = MEMORY;

-- ============================================================
-- Tabela principal: documentos indexaveis
-- ============================================================
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,         -- 'note' | 'memory' | 'skill' | 'session' | 'manifest'
    source_path TEXT NOT NULL,         -- path relativo a raiz de cada fonte
    title TEXT,
    content TEXT NOT NULL,             -- corpo markdown (sem frontmatter)
    tags TEXT,                         -- JSON array: ["tag1", "tag2"]
    frontmatter TEXT,                  -- JSON completo do YAML
    content_hash TEXT NOT NULL,        -- sha1 do content -- detecta mudanca sem reparse
    size_bytes INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,
    access_count INTEGER NOT NULL DEFAULT 0,
    relevance_score REAL NOT NULL DEFAULT 1.0,   -- boost aprendido via uso
    deleted_at TIMESTAMP,                         -- soft delete
    UNIQUE(source_type, source_path)
);

CREATE INDEX IF NOT EXISTS idx_docs_source ON documents(source_type, source_path);
CREATE INDEX IF NOT EXISTS idx_docs_hash ON documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_docs_updated ON documents(updated_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_docs_accessed ON documents(last_accessed DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_docs_relevance ON documents(relevance_score DESC) WHERE deleted_at IS NULL;

-- ============================================================
-- FTS5: documents (full-text search com BM25)
-- ============================================================
-- `unicode61 remove_diacritics 2`: trata acentos PT-BR ("persona" == "personá")
-- `prefix '2 3'`: permite busca por prefixo a partir de 2-3 chars (ex: "per*")

CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    title,
    content,
    tags,
    content='documents',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2',
    prefix='2 3'
);

-- Triggers para manter FTS sincronizada com documents
CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents
WHEN new.deleted_at IS NULL BEGIN
    INSERT INTO documents_fts(rowid, title, content, tags)
    VALUES (new.id, new.title, new.content, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, title, content, tags)
    VALUES ('delete', old.id, old.title, old.content, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, title, content, tags)
    VALUES ('delete', old.id, old.title, old.content, old.tags);
    INSERT INTO documents_fts(rowid, title, content, tags)
    SELECT new.id, new.title, new.content, new.tags
    WHERE new.deleted_at IS NULL;
END;

-- ============================================================
-- Chunks: subdivisao de documentos longos (para RAG)
-- ============================================================
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,      -- ordem dentro do doc (0-based)
    heading TEXT,                       -- heading H1/H2/H3 mais proximo
    content TEXT NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    token_estimate INTEGER,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
    UNIQUE(document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    content,
    heading,
    content='chunks',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, content, heading)
    VALUES (new.id, new.content, new.heading);
END;

CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, content, heading)
    VALUES ('delete', old.id, old.content, old.heading);
END;

CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, content, heading)
    VALUES ('delete', old.id, old.content, old.heading);
    INSERT INTO chunks_fts(rowid, content, heading)
    VALUES (new.id, new.content, new.heading);
END;

-- ============================================================
-- Embeddings: vetores para busca semantica
-- ============================================================
-- Armazenados como BLOB (numpy float32 serializado)
-- Modelo padrao: paraphrase-multilingual-MiniLM-L12-v2 (384 dims)
-- sqlite-vec pode ser usado para KNN rapido em escala

CREATE TABLE IF NOT EXISTS embeddings (
    chunk_id INTEGER PRIMARY KEY,
    model TEXT NOT NULL,               -- nome do modelo (para reindex se trocar)
    dim INTEGER NOT NULL,              -- dimensoes do vetor
    vector BLOB NOT NULL,              -- numpy array serializado
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_emb_model ON embeddings(model);

-- ============================================================
-- Grafo de links
-- ============================================================
CREATE TABLE IF NOT EXISTS links (
    from_id INTEGER NOT NULL,
    to_id INTEGER NOT NULL,
    link_type TEXT NOT NULL,           -- 'wikilink' | 'tag_peer' | 'similar'
    weight REAL NOT NULL DEFAULT 1.0,
    PRIMARY KEY (from_id, to_id, link_type),
    FOREIGN KEY(from_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY(to_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_links_from ON links(from_id, link_type);
CREATE INDEX IF NOT EXISTS idx_links_to ON links(to_id, link_type);

-- ============================================================
-- Tags normalizadas (para queries cruzadas eficientes)
-- ============================================================
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS document_tags (
    document_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (document_id, tag_id),
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_doctags_tag ON document_tags(tag_id);

-- ============================================================
-- Telemetria: o que o agente busca/acessa
-- ============================================================
CREATE TABLE IF NOT EXISTS access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    chunk_id INTEGER,
    query TEXT,
    context TEXT NOT NULL,             -- 'search' | 'read' | 'related' | 'bootstrap'
    score REAL,
    session_id TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE SET NULL,
    FOREIGN KEY(chunk_id) REFERENCES chunks(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_log_time ON access_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_log_doc ON access_log(document_id, timestamp DESC);

-- ============================================================
-- Metadados do sistema (versao do schema, ultimo ingest, etc)
-- ============================================================
CREATE TABLE IF NOT EXISTS system_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO system_meta(key, value) VALUES
    ('schema_version', '1.0'),
    ('embedding_model', 'paraphrase-multilingual-MiniLM-L12-v2'),
    ('embedding_dim', '384'),
    ('created_at', datetime('now'));

-- ============================================================
-- Views uteis
-- ============================================================

-- Documentos ativos (nao deletados) com snippet de preview
CREATE VIEW IF NOT EXISTS active_documents AS
SELECT
    id, source_type, source_path, title, tags, frontmatter,
    size_bytes, created_at, updated_at, last_accessed, access_count, relevance_score,
    substr(content, 1, 200) AS preview
FROM documents
WHERE deleted_at IS NULL;

-- Top acessados nos ultimos 30 dias
CREATE VIEW IF NOT EXISTS top_accessed_30d AS
SELECT
    d.id, d.source_path, d.title, d.tags,
    COUNT(l.id) AS accesses,
    MAX(l.timestamp) AS last_access
FROM documents d
INNER JOIN access_log l ON l.document_id = d.id
WHERE l.timestamp > datetime('now', '-30 days')
  AND d.deleted_at IS NULL
GROUP BY d.id
ORDER BY accesses DESC;

-- Orfas: documentos sem links de entrada e sem tags
CREATE VIEW IF NOT EXISTS orphan_documents AS
SELECT d.id, d.source_path, d.title, d.updated_at
FROM documents d
LEFT JOIN links l ON l.to_id = d.id
LEFT JOIN document_tags dt ON dt.document_id = d.id
WHERE d.deleted_at IS NULL
  AND l.to_id IS NULL
  AND dt.document_id IS NULL;
