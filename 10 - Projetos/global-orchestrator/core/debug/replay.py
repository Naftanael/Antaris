from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"JSONL file not found: {file_path}")

    events: list[dict[str, Any]] = []
    with file_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_number}: {exc}") from exc
            if isinstance(payload, dict):
                events.append(payload)
    return events


def replay_by_request_id(
    path: str | Path,
    request_id: str,
) -> list[dict[str, Any]]:
    """
    Returns the chronological list of events for a given request_id.
    """
    events = read_jsonl(path)
    filtered = [
        event
        for event in events
        if isinstance(event.get("payload"), dict)
        and event["payload"].get("request_id") == request_id
    ]
    # JSONL is append-only and already chronological, but this keeps output stable
    # when logs are merged from multiple sources.
    filtered.sort(key=lambda item: item.get("timestamp", ""))
    return filtered


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay events by request_id from a JSONL trace file.")
    parser.add_argument("--file", required=True, help="Path to JSONL trace file")
    parser.add_argument("--request-id", required=True, help="Request ID to replay")
    parser.add_argument("--json", action="store_true", help="Output raw JSON array")
    return parser


def _render_human(events: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for event in events:
        timestamp = event.get("timestamp", "-")
        level = str(event.get("level", "-")).upper()
        name = event.get("name", "-")
        component = event.get("component") or "-"
        lines.append(f"{timestamp} {level} {name} [{component}]")
    return "\n".join(lines)


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    events = replay_by_request_id(args.file, args.request_id)
    if args.json:
        print(json.dumps(events, ensure_ascii=False, indent=2))
        return

    print(_render_human(events))


if __name__ == "__main__":
    main()
