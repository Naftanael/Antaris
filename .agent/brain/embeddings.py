from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Sequence

import numpy as np

from brain_db import connect

DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_BATCH_SIZE = 32


@dataclass(slots=True)
class EmbeddingStats:
    active_chunks: int
    embedded_chunks: int
    stale_chunks: int
    current_model_chunks: int
    other_model_chunks: int
    embedding_models: list[str]


@lru_cache(maxsize=2)
def get_model(model_name: str = DEFAULT_MODEL):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def serialize_vector(vector: np.ndarray) -> bytes:
    arr = np.asarray(vector, dtype=np.float32)
    return arr.tobytes()


def deserialize_vector(blob: bytes, dim: int | None = None) -> np.ndarray:
    arr = np.frombuffer(blob, dtype=np.float32)
    if dim is not None and arr.size != dim:
        raise ValueError(f"expected dim={dim}, got {arr.size}")
    return arr.copy()


def cosine_similarity(query_vector: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    query = np.asarray(query_vector, dtype=np.float32)
    docs = np.asarray(matrix, dtype=np.float32)
    query_norm = np.linalg.norm(query)
    doc_norms = np.linalg.norm(docs, axis=1)
    denom = np.clip(doc_norms * query_norm, 1e-12, None)
    return (docs @ query) / denom


def encode_texts(
    texts: Sequence[str],
    *,
    model_name: str = DEFAULT_MODEL,
    batch_size: int = DEFAULT_BATCH_SIZE,
    normalize: bool = True,
) -> np.ndarray:
    if not texts:
        return np.empty((0, 0), dtype=np.float32)
    model = get_model(model_name)
    vectors = model.encode(
        list(texts),
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=normalize,
        show_progress_bar=False,
    )
    return np.asarray(vectors, dtype=np.float32)


def get_embedding_stats(conn: sqlite3.Connection, model_name: str = DEFAULT_MODEL) -> EmbeddingStats:
    active_chunks = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE d.deleted_at IS NULL
        """
    ).fetchone()["c"]
    embedded_chunks = conn.execute("SELECT COUNT(*) AS c FROM embeddings").fetchone()["c"]
    current_model_chunks = conn.execute(
        "SELECT COUNT(*) AS c FROM embeddings WHERE model = ?",
        (model_name,),
    ).fetchone()["c"]
    stale_chunks = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        LEFT JOIN embeddings e ON e.chunk_id = c.id
        WHERE d.deleted_at IS NULL
          AND (e.chunk_id IS NULL OR e.model != ?)
        """,
        (model_name,),
    ).fetchone()["c"]
    other_model_chunks = conn.execute(
        "SELECT COUNT(*) AS c FROM embeddings WHERE model != ?",
        (model_name,),
    ).fetchone()["c"]
    models = [
        row["model"]
        for row in conn.execute("SELECT DISTINCT model FROM embeddings ORDER BY model")
    ]
    return EmbeddingStats(
        active_chunks=active_chunks,
        embedded_chunks=embedded_chunks,
        stale_chunks=stale_chunks,
        current_model_chunks=current_model_chunks,
        other_model_chunks=other_model_chunks,
        embedding_models=models,
    )


def iter_pending_chunks(
    conn: sqlite3.Connection,
    *,
    model_name: str = DEFAULT_MODEL,
    limit: int | None = None,
) -> list[sqlite3.Row]:
    sql = """
        SELECT c.id, c.document_id, c.heading, c.content
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        LEFT JOIN embeddings e ON e.chunk_id = c.id
        WHERE d.deleted_at IS NULL
          AND (e.chunk_id IS NULL OR e.model != ?)
        ORDER BY d.updated_at DESC, c.document_id, c.chunk_index
    """
    params: list[object] = [model_name]
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    return list(conn.execute(sql, params))


def upsert_embedding(
    conn: sqlite3.Connection,
    *,
    chunk_id: int,
    model_name: str,
    vector: np.ndarray,
) -> None:
    arr = np.asarray(vector, dtype=np.float32)
    conn.execute(
        """
        INSERT INTO embeddings(chunk_id, model, dim, vector)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(chunk_id) DO UPDATE SET
            model=excluded.model,
            dim=excluded.dim,
            vector=excluded.vector,
            created_at=CURRENT_TIMESTAMP
        """,
        (chunk_id, model_name, int(arr.size), serialize_vector(arr)),
    )


def update_system_meta(conn: sqlite3.Connection, model_name: str, dim: int) -> None:
    conn.execute(
        """
        INSERT INTO system_meta(key, value, updated_at)
        VALUES ('embedding_model', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
        """,
        (model_name,),
    )
    conn.execute(
        """
        INSERT INTO system_meta(key, value, updated_at)
        VALUES ('embedding_dim', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
        """,
        (str(dim),),
    )


def build_embeddings(
    *,
    model_name: str = DEFAULT_MODEL,
    limit: int | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict:
    with connect() as conn:
        pending = iter_pending_chunks(conn, model_name=model_name, limit=limit)
        if not pending:
            stats = get_embedding_stats(conn, model_name=model_name)
            return {
                "model": model_name,
                "processed": 0,
                "dim": None,
                "stats": asdict(stats),
            }

        texts = [row["content"] for row in pending]
        vectors = encode_texts(texts, model_name=model_name, batch_size=batch_size)
        dim = int(vectors.shape[1]) if vectors.ndim == 2 and vectors.shape[0] else 0

        for row, vector in zip(pending, vectors, strict=True):
            upsert_embedding(conn, chunk_id=row["id"], model_name=model_name, vector=vector)

        if dim:
            update_system_meta(conn, model_name, dim)

        stats = get_embedding_stats(conn, model_name=model_name)
        return {
            "model": model_name,
            "processed": len(pending),
            "dim": dim,
            "stats": asdict(stats),
        }


def format_stats(stats: EmbeddingStats | dict) -> str:
    payload = stats if isinstance(stats, dict) else asdict(stats)
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build/update chunk embeddings")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="SentenceTransformer model name")
    parser.add_argument("--limit", type=int, default=None, help="Max stale/missing chunks to process")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Embedding batch size")
    parser.add_argument("--stats", action="store_true", help="Show embedding stats and exit")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.stats:
        with connect(readonly=True) as conn:
            stats = get_embedding_stats(conn, model_name=args.model)
        if args.json:
            print(format_stats(stats))
        else:
            print(f"model: {args.model}")
            print(f"active_chunks: {stats.active_chunks}")
            print(f"embedded_chunks: {stats.embedded_chunks}")
            print(f"current_model_chunks: {stats.current_model_chunks}")
            print(f"other_model_chunks: {stats.other_model_chunks}")
            print(f"pending_or_stale: {stats.stale_chunks}")
            print("models_in_db:", ", ".join(stats.embedding_models) if stats.embedding_models else "-")
        return

    result = build_embeddings(
        model_name=args.model,
        limit=args.limit,
        batch_size=args.batch_size,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"model: {result['model']}")
    print(f"processed: {result['processed']}")
    print(f"dim: {result['dim'] or '-'}")
    stats = result["stats"]
    print(f"active_chunks: {stats['active_chunks']}")
    print(f"embedded_chunks: {stats['embedded_chunks']}")
    print(f"current_model_chunks: {stats['current_model_chunks']}")
    print(f"other_model_chunks: {stats['other_model_chunks']}")
    print(f"pending_or_stale: {stats['stale_chunks']}")


if __name__ == "__main__":
    main()
