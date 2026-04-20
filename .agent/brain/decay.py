from __future__ import annotations

import argparse
from pathlib import Path

from brain_db import DB_PATH, connect, init_db

DECAY_FACTOR = 0.90
RECENT_BOOST = 1.10
INBOUND_BOOST = 1.05
MIN_SCORE = 0.2
MAX_SCORE = 5.0


def clamp(value: float, low: float = MIN_SCORE, high: float = MAX_SCORE) -> float:
    return max(low, min(high, value))


def run_decay(db_path: Path) -> dict:
    summary = {
        "documents_seen": 0,
        "decayed": 0,
        "recent_boosted": 0,
        "inbound_boosted": 0,
        "clamped_to_min": 0,
        "clamped_to_max": 0,
        "changed": 0,
        "unchanged": 0,
    }

    with connect(db_path=db_path, readonly=False) as conn:
        thresholds = conn.execute(
            """
            SELECT
                datetime('now', '-90 days') AS decay_cutoff,
                datetime('now', '-30 days') AS recent_cutoff
            """
        ).fetchone()
        decay_cutoff = thresholds["decay_cutoff"]
        recent_cutoff = thresholds["recent_cutoff"]

        rows = conn.execute(
            """
            SELECT
                d.id,
                d.relevance_score,
                d.last_accessed,
                d.updated_at,
                EXISTS(
                    SELECT 1 FROM links l WHERE l.to_id = d.id
                ) AS has_inbound_links
            FROM documents d
            WHERE d.deleted_at IS NULL
            ORDER BY d.id ASC
            """
        ).fetchall()

        for row in rows:
            summary["documents_seen"] += 1
            before = float(row["relevance_score"])
            score = before

            should_decay = row["last_accessed"] is None or row["last_accessed"] < decay_cutoff
            if should_decay:
                score *= DECAY_FACTOR
                summary["decayed"] += 1

            recently_updated = row["updated_at"] is not None and row["updated_at"] >= recent_cutoff
            if recently_updated:
                score *= RECENT_BOOST
                summary["recent_boosted"] += 1

            if bool(row["has_inbound_links"]):
                score *= INBOUND_BOOST
                summary["inbound_boosted"] += 1

            after = clamp(score)
            if after <= MIN_SCORE and before != after:
                summary["clamped_to_min"] += 1
            if after >= MAX_SCORE and before != after:
                summary["clamped_to_max"] += 1

            if abs(after - before) > 1e-9:
                conn.execute(
                    "UPDATE documents SET relevance_score=? WHERE id=?",
                    (after, row["id"]),
                )
                summary["changed"] += 1
            else:
                summary["unchanged"] += 1

        before_after = conn.execute(
            """
            SELECT
                MIN(relevance_score) AS min_score,
                MAX(relevance_score) AS max_score,
                AVG(relevance_score) AS avg_score
            FROM documents
            WHERE deleted_at IS NULL
            """
        ).fetchone()

    summary["score_range"] = {
        "min": before_after["min_score"],
        "max": before_after["max_score"],
        "avg": before_after["avg_score"],
    }
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply weekly relevance-score maintenance")
    parser.add_argument("--db", default=str(DB_PATH), help="Path to brain.db")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db).expanduser()

    if not db_path.exists():
        init_db(db_path)

    with connect(db_path=db_path, readonly=True) as conn:
        before = conn.execute(
            """
            SELECT
                COUNT(*) AS documents,
                MIN(relevance_score) AS min_score,
                MAX(relevance_score) AS max_score,
                AVG(relevance_score) AS avg_score
            FROM documents
            WHERE deleted_at IS NULL
            """
        ).fetchone()

    summary = run_decay(db_path)

    with connect(db_path=db_path, readonly=True) as conn:
        after = conn.execute(
            """
            SELECT
                COUNT(*) AS documents,
                MIN(relevance_score) AS min_score,
                MAX(relevance_score) AS max_score,
                AVG(relevance_score) AS avg_score
            FROM documents
            WHERE deleted_at IS NULL
            """
        ).fetchone()

    print("Weekly maintenance: relevance_score decay/boost")
    print(
        f"Before: docs={before['documents']} min={before['min_score']} max={before['max_score']} avg={before['avg_score']}"
    )
    print(
        f"After:  docs={after['documents']} min={after['min_score']} max={after['max_score']} avg={after['avg_score']}"
    )
    print()
    print(f"Seen: {summary['documents_seen']}")
    print(f"Changed: {summary['changed']}")
    print(f"Unchanged: {summary['unchanged']}")
    print(f"Decayed (last_accessed > 90d or never): {summary['decayed']}")
    print(f"Boosted by recent update (30d): {summary['recent_boosted']}")
    print(f"Boosted by inbound links: {summary['inbound_boosted']}")
    print(f"Clamped to min: {summary['clamped_to_min']}")
    print(f"Clamped to max: {summary['clamped_to_max']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
