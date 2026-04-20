"""
brain_db.py - Core module: connection, schema bootstrap, common utilities.

Used by ingest.py, search.py, watcher.py, decay.py.
Single source of truth for database access patterns.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

# =============================================================
# Paths
# =============================================================

VAULT_DEFAULT = os.environ.get(
    "OBSIDIAN_VAULT_PATH", "/home/antaris/Documentos/Antaris"
)
VAULT = Path(VAULT_DEFAULT)
AGENT_DIR = VAULT / ".agent"
BRAIN_DIR = AGENT_DIR / "brain"
DB_PATH = AGENT_DIR / "brain.db"
SCHEMA_PATH = BRAIN_DIR / "schema.sql"

# Hermes skills path
HERMES_SKILLS_DIR = Path.home() / ".hermes" / "skills"

# Directories to ignore (aligned with obsidian_index.py)
IGNORE_DIRS = {
    ".obsidian", ".git", ".venv", ".smart-env", ".space", ".makemd",
    "__pycache__", "Sem título", "Tags", ".agent", "copilot",
    "node_modules", "dist", "build", ".hermes",
}

# Regexes
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
TAG_RE = re.compile(r"(?:^|\s)#([a-zA-Z0-9_\-/]+)")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:[|#][^\]]*)?\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


# =============================================================
# Connection
# =============================================================

@contextmanager
def connect(db_path: Path = DB_PATH, readonly: bool = False) -> Iterator[sqlite3.Connection]:
    """Open a connection with sane defaults. Ensures schema exists."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if not db_path.exists() and not readonly:
        init_db(db_path)
    uri = f"file:{db_path}?mode=ro" if readonly else None
    conn = sqlite3.connect(str(uri) if uri else str(db_path), uri=bool(uri), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        if not readonly:
            conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path = DB_PATH) -> None:
    """Create DB + apply schema.sql. Idempotent."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema not found: {SCHEMA_PATH}")

    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


# =============================================================
# Parsing helpers
# =============================================================

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter. Returns (metadata_dict, body_without_frontmatter)."""
    m = FRONTMATTER_RE.match(content)
    if not m:
        return {}, content
    fm: dict = {}
    for line in m.group(1).split("\n"):
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    body = content[m.end():]
    return fm, body


def extract_tags(content: str, frontmatter: dict) -> list[str]:
    """Merge frontmatter tags + inline #tags."""
    inline = set(TAG_RE.findall(content))
    fm_tags = frontmatter.get("tags", "")
    if isinstance(fm_tags, str) and fm_tags:
        for t in fm_tags.split(","):
            t = t.strip(" []")
            if t:
                inline.add(t)
    return sorted(inline)


def extract_wikilinks(content: str) -> list[str]:
    return sorted(set(WIKILINK_RE.findall(content)))


def content_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()


def chunk_by_headings(content: str, max_chars: int = 2000) -> list[dict]:
    """
    Split content into semantic chunks:
    - Prefer splits at H1/H2/H3 boundaries
    - If a section exceeds max_chars, split by paragraph
    - Each chunk carries its nearest heading for context
    """
    lines = content.split("\n")
    chunks: list[dict] = []
    current: list[str] = []
    current_heading: Optional[str] = None
    current_start = 1

    def flush(end_line: int) -> None:
        nonlocal current
        if not current:
            return
        text = "\n".join(current).strip()
        if text:
            chunks.append({
                "heading": current_heading,
                "content": text,
                "start_line": current_start,
                "end_line": end_line,
                "token_estimate": max(1, len(text) // 4),
            })
        current = []

    for i, line in enumerate(lines, start=1):
        m = HEADING_RE.match(line)
        is_heading = m is not None
        joined_len = sum(len(l) + 1 for l in current)

        if is_heading and current:
            flush(i - 1)
            current_start = i
            current_heading = m.group(2).strip() if m else current_heading
        elif joined_len > max_chars and current:
            flush(i - 1)
            current_start = i

        if is_heading:
            current_heading = m.group(2).strip()
        current.append(line)

    flush(len(lines))

    if not chunks:
        chunks.append({
            "heading": None,
            "content": content.strip(),
            "start_line": 1,
            "end_line": len(lines),
            "token_estimate": max(1, len(content) // 4),
        })
    return chunks


def should_ignore_path(path: Path, root: Path) -> bool:
    """Return True if path should be excluded from indexing."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    for part in rel.parts:
        if part in IGNORE_DIRS or part.startswith("."):
            return True
    return False


# =============================================================
# Document upsert (the core ingest operation)
# =============================================================

def upsert_document(
    conn: sqlite3.Connection,
    *,
    source_type: str,
    source_path: str,
    title: str,
    content: str,
    tags: list[str],
    frontmatter: dict,
    size_bytes: int,
) -> tuple[int, bool]:
    """
    Insert or update a document. Skips update if content_hash unchanged.
    Returns (document_id, was_changed).
    """
    h = content_hash(content)
    cur = conn.execute(
        "SELECT id, content_hash FROM documents WHERE source_type=? AND source_path=?",
        (source_type, source_path),
    )
    row = cur.fetchone()

    tags_json = json.dumps(tags, ensure_ascii=False)
    fm_json = json.dumps(frontmatter, ensure_ascii=False)

    if row is None:
        cur = conn.execute(
            """
            INSERT INTO documents
              (source_type, source_path, title, content, tags, frontmatter,
               content_hash, size_bytes, updated_at, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (source_type, source_path, title, content, tags_json, fm_json, h, size_bytes),
        )
        return cur.lastrowid, True

    if row["content_hash"] == h:
        # Touch indexed_at so we know it was verified, but don't rewrite
        conn.execute(
            "UPDATE documents SET indexed_at=CURRENT_TIMESTAMP WHERE id=?", (row["id"],)
        )
        return row["id"], False

    conn.execute(
        """
        UPDATE documents
           SET title=?, content=?, tags=?, frontmatter=?, content_hash=?,
               size_bytes=?, updated_at=CURRENT_TIMESTAMP, indexed_at=CURRENT_TIMESTAMP,
               deleted_at=NULL
         WHERE id=?
        """,
        (title, content, tags_json, fm_json, h, size_bytes, row["id"]),
    )
    return row["id"], True


def soft_delete_document(conn: sqlite3.Connection, doc_id: int) -> None:
    conn.execute(
        "UPDATE documents SET deleted_at=CURRENT_TIMESTAMP WHERE id=?", (doc_id,)
    )


def upsert_tags(conn: sqlite3.Connection, doc_id: int, tags: list[str]) -> None:
    """Sync tag associations for a document."""
    conn.execute("DELETE FROM document_tags WHERE document_id=?", (doc_id,))
    for tag in tags:
        conn.execute("INSERT OR IGNORE INTO tags(name) VALUES (?)", (tag,))
        row = conn.execute("SELECT id FROM tags WHERE name=?", (tag,)).fetchone()
        if row:
            conn.execute(
                "INSERT OR IGNORE INTO document_tags(document_id, tag_id) VALUES (?, ?)",
                (doc_id, row["id"]),
            )


def replace_chunks(conn: sqlite3.Connection, doc_id: int, chunks: list[dict]) -> list[int]:
    """Delete existing chunks for a doc and insert fresh ones. Returns chunk_ids."""
    conn.execute("DELETE FROM chunks WHERE document_id=?", (doc_id,))
    chunk_ids = []
    for i, ch in enumerate(chunks):
        cur = conn.execute(
            """
            INSERT INTO chunks
              (document_id, chunk_index, heading, content, start_line, end_line, token_estimate)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (doc_id, i, ch.get("heading"), ch["content"],
             ch.get("start_line"), ch.get("end_line"), ch.get("token_estimate")),
        )
        chunk_ids.append(cur.lastrowid)
    return chunk_ids


def resolve_wikilinks_to_ids(
    conn: sqlite3.Connection, from_id: int, wikilinks: list[str]
) -> None:
    """Create 'wikilink' edges in the links table. Matches by title."""
    conn.execute("DELETE FROM links WHERE from_id=? AND link_type='wikilink'", (from_id,))
    for wl in wikilinks:
        row = conn.execute(
            "SELECT id FROM documents WHERE title=? AND deleted_at IS NULL LIMIT 1", (wl,)
        ).fetchone()
        if row and row["id"] != from_id:
            conn.execute(
                """
                INSERT OR REPLACE INTO links(from_id, to_id, link_type, weight)
                VALUES (?, ?, 'wikilink', 1.0)
                """,
                (from_id, row["id"]),
            )


def log_access(
    conn: sqlite3.Connection,
    *,
    document_id: Optional[int] = None,
    chunk_id: Optional[int] = None,
    query: Optional[str] = None,
    context: str = "search",
    score: Optional[float] = None,
    session_id: Optional[str] = None,
) -> None:
    conn.execute(
        """
        INSERT INTO access_log(document_id, chunk_id, query, context, score, session_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (document_id, chunk_id, query, context, score, session_id),
    )
    if document_id:
        conn.execute(
            "UPDATE documents SET access_count=access_count+1, last_accessed=CURRENT_TIMESTAMP WHERE id=?",
            (document_id,),
        )


# =============================================================
# Stats (for dashboards)
# =============================================================

def get_stats(conn: sqlite3.Connection) -> dict:
    rows = {}
    for q, key in [
        ("SELECT COUNT(*) c FROM documents WHERE deleted_at IS NULL", "documents"),
        ("SELECT COUNT(*) c FROM chunks", "chunks"),
        ("SELECT COUNT(*) c FROM embeddings", "embeddings"),
        ("SELECT COUNT(*) c FROM links", "links"),
        ("SELECT COUNT(*) c FROM tags", "tags"),
        ("SELECT COUNT(*) c FROM access_log", "access_events"),
        ("SELECT COUNT(*) c FROM orphan_documents", "orphans"),
    ]:
        rows[key] = conn.execute(q).fetchone()["c"]
    size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
    rows["db_size_bytes"] = size
    return rows


if __name__ == "__main__":
    # CLI: init or show stats
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        init_db()
        print(f"Initialized {DB_PATH}")
    else:
        with connect(readonly=True) as conn:
            print(json.dumps(get_stats(conn), indent=2))
