#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from brain_db import (
    AGENT_DIR,
    DB_PATH,
    HERMES_SKILLS_DIR,
    VAULT,
    chunk_by_headings,
    connect,
    extract_tags,
    extract_wikilinks,
    get_stats,
    parse_frontmatter,
    replace_chunks,
    resolve_wikilinks_to_ids,
    should_ignore_path,
    soft_delete_document,
    upsert_document,
    upsert_tags,
)

MEMORY_DIR = AGENT_DIR / "memory"
MANIFEST_PATH = AGENT_DIR / "context-manifest.md"

CLI_TO_SOURCE_TYPE = {
    "notes": "note",
    "memory": "memory",
    "manifest": "manifest",
    "skills": "skill",
}

SOURCE_TYPE_TO_LABEL = {value: key for key, value in CLI_TO_SOURCE_TYPE.items()}


@dataclass(frozen=True)
class SourceSpec:
    cli_name: str
    source_type: str
    root: Path
    single_file: Path | None = None


@dataclass
class IngestSummary:
    requested_sources: list[str]
    scanned: int = 0
    changed: int = 0
    unchanged: int = 0
    reactivated: int = 0
    soft_deleted: int = 0
    chunks_replaced: int = 0
    wikilink_docs_resolved: int = 0
    errors: list[str] = field(default_factory=list)

    def print(self) -> None:
        parts = [
            f"sources={','.join(self.requested_sources)}",
            f"scanned={self.scanned}",
            f"changed={self.changed}",
            f"unchanged={self.unchanged}",
            f"reactivated={self.reactivated}",
            f"soft_deleted={self.soft_deleted}",
            f"chunks={self.chunks_replaced}",
            f"wikilink_docs={self.wikilink_docs_resolved}",
            f"errors={len(self.errors)}",
        ]
        print("ingest " + " ".join(parts))
        for err in self.errors[:10]:
            print(f"error {err}")
        if len(self.errors) > 10:
            print(f"error ... {len(self.errors) - 10} more")


SOURCE_SPECS = {
    "notes": SourceSpec("notes", "note", VAULT),
    "memory": SourceSpec("memory", "memory", MEMORY_DIR),
    "manifest": SourceSpec("manifest", "manifest", MANIFEST_PATH.parent, single_file=MANIFEST_PATH),
    "skills": SourceSpec("skills", "skill", HERMES_SKILLS_DIR),
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest brain sources into SQLite.")
    parser.add_argument(
        "--source",
        action="append",
        choices=sorted(SOURCE_SPECS.keys()),
        help="Limit ingest to one or more sources.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print database summary stats and exit.",
    )
    return parser.parse_args(argv)


def iter_markdown_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    files: list[Path] = []
    for path in sorted(root.rglob("*.md")):
        if path.is_file() and not should_ignore_path(path, root):
            files.append(path)
    return files


def derive_title(path: Path, frontmatter: dict) -> str:
    for key in ("title", "name"):
        value = frontmatter.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    stem = path.stem.strip()
    if stem.upper() in {"SKILL", "DESCRIPTION", "README", "INDEX"} and path.parent.name:
        return path.parent.name.strip() or stem
    return stem or path.name


def make_source_path(path: Path, spec: SourceSpec) -> str:
    if spec.single_file is not None:
        return path.name
    return path.relative_to(spec.root).as_posix()


def fetch_existing_doc(
    conn: sqlite3.Connection,
    source_type: str,
    source_path: str,
) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT id, content_hash, deleted_at FROM documents WHERE source_type=? AND source_path=?",
        (source_type, source_path),
    ).fetchone()


def reactivate_document(conn: sqlite3.Connection, doc_id: int) -> None:
    conn.execute(
        "UPDATE documents SET deleted_at=NULL, indexed_at=CURRENT_TIMESTAMP WHERE id=?",
        (doc_id,),
    )


def cleanup_soft_deleted_document(conn: sqlite3.Connection, doc_id: int) -> None:
    soft_delete_document(conn, doc_id)
    conn.execute("DELETE FROM chunks WHERE document_id=?", (doc_id,))
    conn.execute("DELETE FROM document_tags WHERE document_id=?", (doc_id,))
    conn.execute("DELETE FROM links WHERE from_id=? OR to_id=?", (doc_id, doc_id))


def index_file(
    conn: sqlite3.Connection,
    spec: SourceSpec,
    path: Path,
    summary: IngestSummary,
) -> tuple[int, list[str], str] | None:
    source_path = make_source_path(path, spec)
    existing = fetch_existing_doc(conn, spec.source_type, source_path)

    try:
        raw_content = path.read_text(encoding="utf-8", errors="replace")
        size_bytes = path.stat().st_size
    except Exception as exc:
        summary.errors.append(f"{spec.cli_name}:{source_path}: {exc}")
        return None

    frontmatter, body = parse_frontmatter(raw_content)
    tags = extract_tags(body, frontmatter)
    wikilinks = extract_wikilinks(body)
    title = derive_title(path, frontmatter)

    doc_id, was_changed = upsert_document(
        conn,
        source_type=spec.source_type,
        source_path=source_path,
        title=title,
        content=body,
        tags=tags,
        frontmatter=frontmatter,
        size_bytes=size_bytes,
    )

    was_deleted = bool(existing and existing["deleted_at"])
    if was_deleted:
        reactivate_document(conn, doc_id)
        summary.reactivated += 1

    if was_changed:
        summary.changed += 1
    else:
        summary.unchanged += 1

    if was_changed or was_deleted or existing is None:
        upsert_tags(conn, doc_id, tags)
        chunks = chunk_by_headings(body)
        replace_chunks(conn, doc_id, chunks)
        summary.chunks_replaced += len(chunks)

    summary.scanned += 1
    return doc_id, wikilinks, source_path


def discover_paths(spec: SourceSpec) -> list[Path]:
    if spec.single_file is not None:
        return [spec.single_file] if spec.single_file.exists() else []
    return list(iter_markdown_files(spec.root))


def soft_delete_missing(
    conn: sqlite3.Connection,
    source_type: str,
    seen_paths: set[str],
) -> int:
    rows = conn.execute(
        "SELECT id, source_path FROM documents WHERE source_type=? AND deleted_at IS NULL",
        (source_type,),
    ).fetchall()
    deleted = 0
    for row in rows:
        if row["source_path"] not in seen_paths:
            cleanup_soft_deleted_document(conn, row["id"])
            deleted += 1
    return deleted


def resolve_all_wikilinks(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        """
        SELECT id, content
        FROM documents
        WHERE deleted_at IS NULL
        """
    ).fetchall()
    resolved = 0
    for row in rows:
        resolve_wikilinks_to_ids(conn, row["id"], extract_wikilinks(row["content"] or ""))
        resolved += 1
    return resolved


def update_last_ingest_meta(conn: sqlite3.Connection, sources: list[str]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO system_meta(key, value, updated_at)
        VALUES ('last_ingest_at', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
        """,
        (now,),
    )
    conn.execute(
        """
        INSERT INTO system_meta(key, value, updated_at)
        VALUES ('last_ingest_sources', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
        """,
        (",".join(sources),),
    )


def run_ingest(cli_sources: list[str]) -> int:
    selected = cli_sources or ["notes", "memory", "manifest", "skills"]
    specs = [SOURCE_SPECS[name] for name in selected]
    summary = IngestSummary(requested_sources=selected)

    with connect() as conn:
        for spec in specs:
            seen_paths: set[str] = set()
            for path in discover_paths(spec):
                result = index_file(conn, spec, path, summary)
                if result is None:
                    continue
                _, _, source_path = result
                seen_paths.add(source_path)

            summary.soft_deleted += soft_delete_missing(conn, spec.source_type, seen_paths)

        summary.wikilink_docs_resolved = resolve_all_wikilinks(conn)
        update_last_ingest_meta(conn, selected)

    summary.print()
    return 0 if not summary.errors else 1


def print_stats() -> int:
    with connect(readonly=True) as conn:
        stats = get_stats(conn)
        total_docs = conn.execute("SELECT COUNT(*) AS c FROM documents").fetchone()["c"]
        deleted_docs = conn.execute(
            "SELECT COUNT(*) AS c FROM documents WHERE deleted_at IS NOT NULL"
        ).fetchone()["c"]
        print(
            "stats"
            f" documents_active={stats['documents']}"
            f" documents_total={total_docs}"
            f" documents_deleted={deleted_docs}"
            f" chunks={stats['chunks']}"
            f" links={stats['links']}"
            f" tags={stats['tags']}"
            f" embeddings={stats['embeddings']}"
            f" access_events={stats['access_events']}"
            f" orphans={stats['orphans']}"
            f" db_size_bytes={stats['db_size_bytes']}"
            f" db_path={DB_PATH}"
        )

        rows = conn.execute(
            """
            SELECT source_type,
                   SUM(CASE WHEN deleted_at IS NULL THEN 1 ELSE 0 END) AS active_count,
                   SUM(CASE WHEN deleted_at IS NOT NULL THEN 1 ELSE 0 END) AS deleted_count
            FROM documents
            GROUP BY source_type
            ORDER BY source_type
            """
        ).fetchall()

        if rows:
            formatted = []
            for row in rows:
                label = SOURCE_TYPE_TO_LABEL.get(row["source_type"], row["source_type"])
                active_count = row["active_count"] or 0
                deleted_count = row["deleted_count"] or 0
                formatted.append(f"{label}={active_count}/{deleted_count}")
            print("sources active/deleted " + " ".join(formatted))
        else:
            print("sources active/deleted none")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.stats:
        return print_stats()
    return run_ingest(args.source)


if __name__ == "__main__":
    raise SystemExit(main())
