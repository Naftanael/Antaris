from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import textwrap
import uuid
from collections import defaultdict
from dataclasses import dataclass
from typing import Sequence

import numpy as np

import brain_db
from brain_db import connect
from embeddings import DEFAULT_MODEL, cosine_similarity, deserialize_vector, encode_texts

DEFAULT_LIMIT = 5
LEXICAL_CANDIDATES = 50
SEMANTIC_CANDIDATES = 100
RRF_K = 60.0


@dataclass(slots=True)
class SearchHit:
    chunk_id: int
    document_id: int
    title: str | None
    path: str
    source_type: str
    heading: str | None
    content: str
    score: float
    lexical_score: float | None = None
    semantic_score: float | None = None

    def to_dict(self, *, query: str | None = None, snippet_length: int = 220) -> dict:
        return {
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "title": self.title,
            "path": self.path,
            "source_type": self.source_type,
            "heading": self.heading,
            "score": round(float(self.score), 6),
            "lexical_score": None if self.lexical_score is None else round(float(self.lexical_score), 6),
            "semantic_score": None if self.semantic_score is None else round(float(self.semantic_score), 6),
            "snippet": make_snippet(self.content, query=query, length=snippet_length),
        }


def make_snippet(text: str, query: str | None = None, length: int = 220) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        return ""
    if not query:
        return textwrap.shorten(cleaned, width=length, placeholder="…")

    lowered = cleaned.lower()
    terms = [term for term in query.lower().split() if len(term) >= 2]
    pos = min((lowered.find(term) for term in terms if lowered.find(term) >= 0), default=-1)
    if pos < 0:
        return textwrap.shorten(cleaned, width=length, placeholder="…")

    start = max(0, pos - length // 3)
    end = min(len(cleaned), start + length)
    snippet = cleaned[start:end].strip()
    if start > 0:
        snippet = "…" + snippet
    if end < len(cleaned):
        snippet += "…"
    return snippet


def lexical_search(conn: sqlite3.Connection, query: str, limit: int = DEFAULT_LIMIT) -> list[SearchHit]:
    sql = """
        WITH ranked AS (
            SELECT
                c.id AS chunk_id,
                d.id AS document_id,
                d.title,
                d.source_path,
                d.source_type,
                c.heading,
                c.content,
                bm25(chunks_fts, 5.0, 2.0) AS bm25_score,
                d.relevance_score,
                d.access_count
            FROM chunks_fts
            JOIN chunks c ON c.id = chunks_fts.rowid
            JOIN documents d ON d.id = c.document_id
            WHERE chunks_fts MATCH ?
              AND d.deleted_at IS NULL
        )
        SELECT *
        FROM ranked
        ORDER BY bm25_score ASC, relevance_score DESC, access_count DESC
        LIMIT ?
    """
    rows = conn.execute(sql, (query, limit)).fetchall()
    hits: list[SearchHit] = []
    total = max(len(rows), 1)
    for rank, row in enumerate(rows, start=1):
        lexical_score = (total - rank + 1) / total
        hits.append(
            SearchHit(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                title=row["title"],
                path=row["source_path"],
                source_type=row["source_type"],
                heading=row["heading"],
                content=row["content"],
                score=lexical_score,
                lexical_score=lexical_score,
                semantic_score=None,
            )
        )
    return hits


def fetch_embedding_rows(
    conn: sqlite3.Connection,
    *,
    model_name: str = DEFAULT_MODEL,
    limit: int | None = None,
) -> list[sqlite3.Row]:
    sql = """
        SELECT
            c.id AS chunk_id,
            d.id AS document_id,
            d.title,
            d.source_path,
            d.source_type,
            c.heading,
            c.content,
            e.dim,
            e.vector,
            d.relevance_score,
            d.access_count
        FROM embeddings e
        JOIN chunks c ON c.id = e.chunk_id
        JOIN documents d ON d.id = c.document_id
        WHERE e.model = ?
          AND d.deleted_at IS NULL
        ORDER BY d.relevance_score DESC, d.access_count DESC, c.id
    """
    params: list[object] = [model_name]
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    return list(conn.execute(sql, params))


def semantic_search(
    conn: sqlite3.Connection,
    query: str,
    *,
    limit: int = DEFAULT_LIMIT,
    model_name: str = DEFAULT_MODEL,
    candidate_limit: int = SEMANTIC_CANDIDATES,
) -> list[SearchHit]:
    rows = fetch_embedding_rows(conn, model_name=model_name, limit=candidate_limit)
    if not rows:
        return []

    query_vector = encode_texts([query], model_name=model_name)[0]
    matrix = np.vstack([deserialize_vector(row["vector"], row["dim"]) for row in rows])
    scores = cosine_similarity(query_vector, matrix)

    by_document: dict[int, tuple[float, sqlite3.Row]] = {}
    for idx, row in enumerate(rows):
        semantic_score = float(scores[idx])
        current = by_document.get(row["document_id"])
        if current is None or semantic_score > current[0]:
            by_document[row["document_id"]] = (semantic_score, row)

    ranked = sorted(by_document.values(), key=lambda item: item[0], reverse=True)[:limit]
    hits: list[SearchHit] = []
    for semantic_score, row in ranked:
        hits.append(
            SearchHit(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                title=row["title"],
                path=row["source_path"],
                source_type=row["source_type"],
                heading=row["heading"],
                content=row["content"],
                score=semantic_score,
                lexical_score=None,
                semantic_score=semantic_score,
            )
        )
    return hits


def reciprocal_rank_fusion(*ranked_lists: Sequence[SearchHit], limit: int = DEFAULT_LIMIT) -> list[SearchHit]:
    merged: dict[int, SearchHit] = {}
    rrf_scores: defaultdict[int, float] = defaultdict(float)

    for ranked in ranked_lists:
        for rank, hit in enumerate(ranked, start=1):
            rrf_scores[hit.chunk_id] += 1.0 / (RRF_K + rank)
            existing = merged.get(hit.chunk_id)
            if existing is None:
                merged[hit.chunk_id] = SearchHit(
                    chunk_id=hit.chunk_id,
                    document_id=hit.document_id,
                    title=hit.title,
                    path=hit.path,
                    source_type=hit.source_type,
                    heading=hit.heading,
                    content=hit.content,
                    score=hit.score,
                    lexical_score=hit.lexical_score,
                    semantic_score=hit.semantic_score,
                )
            else:
                if hit.lexical_score is not None:
                    existing.lexical_score = hit.lexical_score
                if hit.semantic_score is not None:
                    existing.semantic_score = hit.semantic_score

    fused = []
    for chunk_id, hit in merged.items():
        hit.score = rrf_scores[chunk_id]
        fused.append(hit)
    fused.sort(
        key=lambda item: (
            item.score,
            item.semantic_score if item.semantic_score is not None else -1.0,
            item.lexical_score if item.lexical_score is not None else -1.0,
        ),
        reverse=True,
    )
    return fused[:limit]


def hybrid_search(
    conn: sqlite3.Connection,
    query: str,
    *,
    limit: int = DEFAULT_LIMIT,
    model_name: str = DEFAULT_MODEL,
) -> list[SearchHit]:
    lexical_hits = lexical_search(conn, query, limit=max(limit, LEXICAL_CANDIDATES))
    semantic_hits = semantic_search(
        conn,
        query,
        limit=max(limit, SEMANTIC_CANDIDATES // 2),
        model_name=model_name,
        candidate_limit=SEMANTIC_CANDIDATES,
    )
    return reciprocal_rank_fusion(lexical_hits, semantic_hits, limit=limit)


def log_hits(
    conn: sqlite3.Connection,
    hits: Sequence[SearchHit],
    *,
    query: str | None,
    context: str,
    session_id: str | None = None,
) -> None:
    sid = session_id or str(uuid.uuid4())
    for hit in hits:
        brain_db.log_access(
            conn,
            document_id=hit.document_id,
            chunk_id=hit.chunk_id,
            query=query,
            context=context,
            score=hit.score,
            session_id=sid,
        )


def run_query(
    query: str,
    *,
    limit: int = DEFAULT_LIMIT,
    mode: str = "hybrid",
    model_name: str = DEFAULT_MODEL,
    log_results: bool = True,
) -> list[SearchHit]:
    with connect() as conn:
        if mode == "lexical":
            hits = lexical_search(conn, query, limit=limit)
        elif mode == "semantic":
            try:
                hits = semantic_search(conn, query, limit=limit, model_name=model_name)
            except ModuleNotFoundError as exc:
                print(
                    f"warning: semantic search unavailable ({exc}); falling back to lexical mode",
                    file=sys.stderr,
                )
                hits = lexical_search(conn, query, limit=limit)
        elif mode == "hybrid":
            try:
                hits = hybrid_search(conn, query, limit=limit, model_name=model_name)
            except ModuleNotFoundError as exc:
                print(
                    f"warning: hybrid search unavailable ({exc}); falling back to lexical mode",
                    file=sys.stderr,
                )
                hits = lexical_search(conn, query, limit=limit)
        else:
            raise ValueError(f"unsupported mode: {mode}")

        if log_results and hits:
            log_hits(conn, hits, query=query, context=f"search:{mode}")
        return hits


def recent_documents(days: int, limit: int = DEFAULT_LIMIT) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, title, source_path, source_type, updated_at, indexed_at
            FROM documents
            WHERE deleted_at IS NULL
              AND updated_at >= datetime('now', ?)
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (f"-{days} days", limit),
        ).fetchall()
        docs = [dict(row) for row in rows]
        for row in rows:
            brain_db.log_access(
                conn,
                document_id=row["id"],
                context="recent",
                session_id=str(uuid.uuid4()),
            )
        return docs


def related_documents(title: str, limit: int = DEFAULT_LIMIT) -> list[dict]:
    with connect() as conn:
        source = conn.execute(
            """
            SELECT id, title, tags, content
            FROM documents
            WHERE deleted_at IS NULL
              AND title = ?
            LIMIT 1
            """,
            (title,),
        ).fetchone()
        if source is None:
            return []

        related = conn.execute(
            """
            WITH base_tags AS (
                SELECT tag_id FROM document_tags WHERE document_id = ?
            ),
            tag_related AS (
                SELECT
                    d.id,
                    d.title,
                    d.source_path,
                    d.source_type,
                    COUNT(*) AS shared_tags,
                    MAX(d.last_accessed) AS last_accessed
                FROM document_tags dt
                JOIN base_tags bt ON bt.tag_id = dt.tag_id
                JOIN documents d ON d.id = dt.document_id
                WHERE d.deleted_at IS NULL
                  AND d.id != ?
                GROUP BY d.id
            ),
            link_related AS (
                SELECT
                    CASE WHEN l.from_id = ? THEN l.to_id ELSE l.from_id END AS document_id,
                    SUM(l.weight) AS link_weight
                FROM links l
                WHERE (l.from_id = ? OR l.to_id = ?)
                GROUP BY 1
            )
            SELECT
                d.id,
                d.title,
                d.source_path,
                d.source_type,
                COALESCE(tr.shared_tags, 0) AS shared_tags,
                COALESCE(lr.link_weight, 0.0) AS link_weight,
                d.updated_at,
                d.last_accessed,
                (COALESCE(tr.shared_tags, 0) * 2.0) + COALESCE(lr.link_weight, 0.0) AS score
            FROM documents d
            LEFT JOIN tag_related tr ON tr.id = d.id
            LEFT JOIN link_related lr ON lr.document_id = d.id
            WHERE d.deleted_at IS NULL
              AND d.id != ?
              AND (COALESCE(tr.shared_tags, 0) > 0 OR COALESCE(lr.link_weight, 0.0) > 0)
            ORDER BY score DESC, d.updated_at DESC
            LIMIT ?
            """,
            (source["id"], source["id"], source["id"], source["id"], source["id"], source["id"], limit),
        ).fetchall()
        docs = [dict(row) for row in related]
        session_id = str(uuid.uuid4())
        for row in related:
            brain_db.log_access(
                conn,
                document_id=row["id"],
                query=title,
                context="related",
                score=row["score"],
                session_id=session_id,
            )
        return docs


def top_accessed(days: int, limit: int = DEFAULT_LIMIT) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT
                d.id,
                d.title,
                d.source_path,
                d.source_type,
                COUNT(al.id) AS accesses,
                MAX(al.timestamp) AS last_accessed
            FROM access_log al
            JOIN documents d ON d.id = al.document_id
            WHERE d.deleted_at IS NULL
              AND al.timestamp >= datetime('now', ?)
            GROUP BY d.id
            ORDER BY accesses DESC, last_accessed DESC
            LIMIT ?
            """,
            (f"-{days} days", limit),
        ).fetchall()
        docs = [dict(row) for row in rows]
        for row in rows:
            brain_db.log_access(
                conn,
                document_id=row["id"],
                context="top-accessed",
                score=float(row["accesses"]),
                session_id=str(uuid.uuid4()),
            )
        return docs


def print_hits(hits: Sequence[SearchHit], *, query: str | None = None) -> None:
    for idx, hit in enumerate(hits, start=1):
        payload = hit.to_dict(query=query)
        print(f"[{idx}] {payload['title'] or '(sem título)'}")
        print(f"  path: {payload['path']}")
        print(f"  source_type: {payload['source_type']}")
        print(f"  heading: {payload['heading'] or '-'}")
        print(f"  score: {payload['score']}")
        if payload["lexical_score"] is not None or payload["semantic_score"] is not None:
            print(
                f"  lexical_score: {payload['lexical_score'] if payload['lexical_score'] is not None else '-'}"
                f" | semantic_score: {payload['semantic_score'] if payload['semantic_score'] is not None else '-'}"
            )
        print(f"  snippet: {payload['snippet']}")
        print()


def print_json(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hybrid retrieval over brain.db")
    subparsers = parser.add_subparsers(dest="command", required=True)

    query_parser = subparsers.add_parser("query", help="Search indexed chunks")
    query_parser.add_argument("query")
    query_parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    query_parser.add_argument("--mode", choices=["lexical", "semantic", "hybrid"], default="hybrid")
    query_parser.add_argument("--model", default=DEFAULT_MODEL)
    query_parser.add_argument("--json", action="store_true")
    query_parser.add_argument("--no-log", action="store_true")

    recent_parser = subparsers.add_parser("recent", help="Recent documents")
    recent_parser.add_argument("--days", type=int, default=7)
    recent_parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    recent_parser.add_argument("--json", action="store_true")

    related_parser = subparsers.add_parser("related", help="Related documents by title")
    related_parser.add_argument("--title", required=True)
    related_parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    related_parser.add_argument("--json", action="store_true")

    top_parser = subparsers.add_parser("top-accessed", help="Most accessed docs")
    top_parser.add_argument("--days", type=int, default=30)
    top_parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    top_parser.add_argument("--json", action="store_true")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "query":
        hits = run_query(
            args.query,
            limit=args.limit,
            mode=args.mode,
            model_name=args.model,
            log_results=not args.no_log,
        )
        if args.json:
            print_json([hit.to_dict(query=args.query) for hit in hits])
        else:
            print_hits(hits, query=args.query)
        return

    if args.command == "recent":
        docs = recent_documents(days=args.days, limit=args.limit)
        if args.json:
            print_json(docs)
        else:
            for doc in docs:
                print(f"- {doc['title'] or '(sem título)'} [{doc['source_type']}] {doc['source_path']} :: updated_at={doc['updated_at']}")
        return

    if args.command == "related":
        docs = related_documents(args.title, limit=args.limit)
        if args.json:
            print_json(docs)
        else:
            for doc in docs:
                print(
                    f"- {doc['title'] or '(sem título)'} [{doc['source_type']}] {doc['source_path']}"
                    f" :: score={round(float(doc['score']), 6)} shared_tags={doc['shared_tags']} link_weight={doc['link_weight']}"
                )
        return

    if args.command == "top-accessed":
        docs = top_accessed(days=args.days, limit=args.limit)
        if args.json:
            print_json(docs)
        else:
            for doc in docs:
                print(
                    f"- {doc['title'] or '(sem título)'} [{doc['source_type']}] {doc['source_path']}"
                    f" :: accesses={doc['accesses']} last_accessed={doc['last_accessed']}"
                )
        return


if __name__ == "__main__":
    main()
