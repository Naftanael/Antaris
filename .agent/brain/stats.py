from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from brain_db import DB_PATH, connect, get_stats, init_db


def human_bytes(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
        value /= 1024.0
    return f"{size} B"


def rows_to_dicts(rows) -> list[dict]:
    return [dict(row) for row in rows]


def build_dashboard(db_path: Path) -> dict:
    with connect(db_path=db_path, readonly=True) as conn:
        totals = get_stats(conn)

        counts_by_source_type = rows_to_dicts(
            conn.execute(
                """
                SELECT source_type, COUNT(*) AS count
                FROM documents
                WHERE deleted_at IS NULL
                GROUP BY source_type
                ORDER BY count DESC, source_type ASC
                """
            ).fetchall()
        )

        top_tags = rows_to_dicts(
            conn.execute(
                """
                SELECT t.name AS tag, COUNT(*) AS count
                FROM tags t
                INNER JOIN document_tags dt ON dt.tag_id = t.id
                INNER JOIN documents d ON d.id = dt.document_id
                WHERE d.deleted_at IS NULL
                GROUP BY t.id, t.name
                ORDER BY count DESC, tag ASC
                LIMIT 10
                """
            ).fetchall()
        )

        top_accessed_docs = rows_to_dicts(
            conn.execute(
                """
                SELECT
                    d.id,
                    COALESCE(NULLIF(d.title, ''), d.source_path) AS title,
                    d.source_type,
                    d.source_path,
                    d.access_count,
                    d.last_accessed,
                    d.relevance_score
                FROM documents d
                WHERE d.deleted_at IS NULL
                ORDER BY d.access_count DESC, d.last_accessed DESC, d.relevance_score DESC
                LIMIT 10
                """
            ).fetchall()
        )

        recent_ingest_docs = rows_to_dicts(
            conn.execute(
                """
                SELECT
                    d.id,
                    COALESCE(NULLIF(d.title, ''), d.source_path) AS title,
                    d.source_type,
                    d.source_path,
                    d.indexed_at,
                    d.updated_at
                FROM documents d
                WHERE d.deleted_at IS NULL
                ORDER BY d.indexed_at DESC, d.updated_at DESC
                LIMIT 10
                """
            ).fetchall()
        )

        ingest_counts = dict(
            conn.execute(
                """
                SELECT 'last_24h' AS bucket, COUNT(*) AS count
                FROM documents
                WHERE deleted_at IS NULL AND indexed_at >= datetime('now', '-1 day')
                UNION ALL
                SELECT 'last_7d' AS bucket, COUNT(*) AS count
                FROM documents
                WHERE deleted_at IS NULL AND indexed_at >= datetime('now', '-7 days')
                UNION ALL
                SELECT 'last_30d' AS bucket, COUNT(*) AS count
                FROM documents
                WHERE deleted_at IS NULL AND indexed_at >= datetime('now', '-30 days')
                """
            ).fetchall()
        )

        orphan_count = conn.execute(
            "SELECT COUNT(*) AS count FROM orphan_documents"
        ).fetchone()["count"]

        inbound_link_stats = dict(
            conn.execute(
                """
                SELECT
                    SUM(CASE WHEN inbound_count > 0 THEN 1 ELSE 0 END) AS linked_documents,
                    SUM(CASE WHEN inbound_count = 0 THEN 1 ELSE 0 END) AS unlinked_documents
                FROM (
                    SELECT d.id, COUNT(l.to_id) AS inbound_count
                    FROM documents d
                    LEFT JOIN links l ON l.to_id = d.id
                    WHERE d.deleted_at IS NULL
                    GROUP BY d.id
                )
                """
            ).fetchone()
        )

    size_bytes = db_path.stat().st_size if db_path.exists() else 0

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_path": str(db_path),
        "db_size_bytes": size_bytes,
        "db_size_human": human_bytes(size_bytes),
        "totals": totals,
        "counts_by_source_type": counts_by_source_type,
        "top_tags": top_tags,
        "top_accessed_docs": top_accessed_docs,
        "recent_ingest_activity": {
            "counts": ingest_counts,
            "documents": recent_ingest_docs,
        },
        "orphan_count": orphan_count,
        "link_health": inbound_link_stats,
    }


def print_human(dashboard: dict) -> None:
    totals = dashboard["totals"]
    print("Brain dashboard")
    print(f"DB: {dashboard['db_path']}")
    print(f"Size: {dashboard['db_size_human']} ({dashboard['db_size_bytes']} bytes)")
    print(f"Generated: {dashboard['generated_at']}")
    print()

    print("Totals")
    print(f"  Documents: {totals.get('documents', 0)}")
    print(f"  Chunks: {totals.get('chunks', 0)}")
    print(f"  Embeddings: {totals.get('embeddings', 0)}")
    print(f"  Links: {totals.get('links', 0)}")
    print(f"  Tags: {totals.get('tags', 0)}")
    print(f"  Access events: {totals.get('access_events', 0)}")
    print(f"  Orphans: {dashboard['orphan_count']}")
    print()

    print("Counts by source_type")
    if dashboard["counts_by_source_type"]:
        for row in dashboard["counts_by_source_type"]:
            print(f"  {row['source_type']}: {row['count']}")
    else:
        print("  No indexed documents")
    print()

    print("Top tags")
    if dashboard["top_tags"]:
        for row in dashboard["top_tags"]:
            print(f"  #{row['tag']}: {row['count']}")
    else:
        print("  No tags recorded")
    print()

    print("Top accessed docs")
    if dashboard["top_accessed_docs"]:
        for row in dashboard["top_accessed_docs"]:
            print(
                f"  {row['access_count']:>4}  {row['title']}"
                f" [{row['source_type']}]"
                f" last_accessed={row['last_accessed'] or '-'}"
            )
    else:
        print("  No access history yet")
    print()

    recent = dashboard["recent_ingest_activity"]
    counts = recent["counts"]
    print("Recent ingest activity")
    print(
        "  "
        f"24h={counts.get('last_24h', 0)}  "
        f"7d={counts.get('last_7d', 0)}  "
        f"30d={counts.get('last_30d', 0)}"
    )
    if recent["documents"]:
        for row in recent["documents"]:
            print(
                f"  {row['indexed_at'] or '-'}  {row['title']}"
                f" [{row['source_type']}]"
            )
    else:
        print("  No recent ingest records")
    print()

    link_health = dashboard["link_health"]
    print("Link health")
    print(f"  Linked docs: {link_health.get('linked_documents', 0) or 0}")
    print(f"  Unlinked docs: {link_health.get('unlinked_documents', 0) or 0}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show a dashboard for brain.db")
    parser.add_argument("--db", default=str(DB_PATH), help="Path to brain.db")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db).expanduser()
    if not db_path.exists():
        init_db(db_path)
    dashboard = build_dashboard(db_path)

    if args.json:
        print(json.dumps(dashboard, indent=2, ensure_ascii=False))
    else:
        print_human(dashboard)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
