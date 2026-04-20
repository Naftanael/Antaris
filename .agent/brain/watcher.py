from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Iterable

from brain_db import HERMES_SKILLS_DIR, IGNORE_DIRS, VAULT

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
except ImportError:  # pragma: no cover - optional dependency
    FileSystemEventHandler = object  # type: ignore[assignment]
    Observer = None

WATCH_EXTENSIONS = {".md", ".markdown", ".txt", ".json", ".yaml", ".yml"}
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PYTHON = SCRIPT_DIR / ".venv" / "bin" / "python"
INGEST_SCRIPT = SCRIPT_DIR / "ingest.py"


class WatcherRuntimeError(RuntimeError):
    pass


class IngestRunner:
    def __init__(self, python_executable: Path, debounce_seconds: float) -> None:
        self.python_executable = python_executable
        self.debounce_seconds = debounce_seconds
        self.lock = threading.Lock()
        self.pending: dict[str, float] = {}
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        if self.thread is not None:
            return
        self.thread = threading.Thread(target=self._loop, name="ingest-runner", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=max(1.0, self.debounce_seconds + 2.0))

    def schedule(self, source_name: str) -> None:
        when = time.monotonic() + self.debounce_seconds
        with self.lock:
            self.pending[source_name] = when
        print(f"queued ingest: {source_name}", flush=True)

    def schedule_full(self, reason: str) -> None:
        when = time.monotonic() + self.debounce_seconds
        key = f"__full__:{reason}"
        with self.lock:
            self.pending[key] = when
        print(f"queued full ingest: {reason}", flush=True)

    def run_once(self, targets: list[str]) -> int:
        rc = 0
        full_requested = any(target.startswith("__full__:") for target in targets)
        if full_requested:
            return self._invoke([])

        for source_name in sorted(set(targets)):
            current = self._invoke(["--source", source_name])
            rc = current if current != 0 else rc
        return rc

    def _loop(self) -> None:
        while not self.stop_event.is_set():
            due = self._collect_due()
            if due:
                self.run_once(due)
                continue
            self.stop_event.wait(0.5)

    def _collect_due(self) -> list[str]:
        now = time.monotonic()
        with self.lock:
            full_due = [item for item, ts in self.pending.items() if item.startswith("__full__:") and ts <= now]
            if full_due:
                self.pending.clear()
                return [full_due[-1]]

            due = [item for item, ts in self.pending.items() if ts <= now]
            for item in due:
                self.pending.pop(item, None)
        return due

    def _invoke(self, extra_args: list[str]) -> int:
        if not INGEST_SCRIPT.exists():
            print(
                f"warning: ingest script not found at {INGEST_SCRIPT}; skipping {extra_args or ['full']}",
                flush=True,
            )
            return 0

        cmd = [str(self.python_executable), str(INGEST_SCRIPT), *extra_args]
        print(f"running: {' '.join(cmd)}", flush=True)
        completed = subprocess.run(cmd, cwd=str(SCRIPT_DIR), check=False)
        if completed.returncode != 0:
            print(f"ingest failed with exit code {completed.returncode}", flush=True)
        return completed.returncode


class DebouncedEventHandler(FileSystemEventHandler):
    def __init__(self, runtime: IngestRunner, watch_roots: list[tuple[str, Path]]) -> None:
        self.runtime = runtime
        self.watch_roots = watch_roots

    def on_any_event(self, event) -> None:  # pragma: no cover - exercised via watchdog runtime
        if getattr(event, "is_directory", False):
            return
        for candidate in [getattr(event, "src_path", None), getattr(event, "dest_path", None)]:
            if not candidate:
                continue
            source_name = classify_path(Path(candidate), self.watch_roots)
            if source_name is not None:
                self.runtime.schedule(source_name)


def is_relevant_file(path: Path) -> bool:
    if path.name.startswith('.'):
        return False
    return path.suffix.lower() in WATCH_EXTENSIONS


def iter_relevant_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    results: list[Path] = []
    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith('.')]
        current = Path(current_root)
        for name in filenames:
            path = current / name
            if is_relevant_file(path):
                results.append(path)
    return results


def determine_paths() -> list[tuple[str, Path]]:
    return [
        ("memory", VAULT / ".agent" / "memory"),
        ("notes", VAULT),
        ("skills", HERMES_SKILLS_DIR),
    ]


def classify_path(path: Path, watch_roots: list[tuple[str, Path]]) -> str | None:
    try:
        path = path.resolve()
    except FileNotFoundError:
        path = path.absolute()

    for source_name, root in watch_roots:
        try:
            rel = path.relative_to(root.resolve())
        except ValueError:
            continue
        if any(part in IGNORE_DIRS or part.startswith('.') for part in rel.parts[:-1]):
            continue
        if not is_relevant_file(path):
            continue
        return source_name
    return None


def poll_once(watch_roots: list[tuple[str, Path]]) -> list[str]:
    changed: set[str] = set()
    for source_name, root in watch_roots:
        for path in iter_relevant_files(root):
            classified = classify_path(path, [(source_name, root)])
            if classified is not None:
                changed.add(classified)
    return sorted(changed)


def snapshot_paths(watch_roots: list[tuple[str, Path]]) -> dict[Path, tuple[int, int]]:
    snapshot: dict[Path, tuple[int, int]] = {}
    for _, root in watch_roots:
        for path in iter_relevant_files(root):
            try:
                stat = path.stat()
            except FileNotFoundError:
                continue
            snapshot[path.resolve()] = (stat.st_mtime_ns, stat.st_size)
    return snapshot


def diff_snapshots(
    previous: dict[Path, tuple[int, int]],
    current: dict[Path, tuple[int, int]],
    watch_roots: list[tuple[str, Path]],
) -> list[str]:
    changed_paths = set(previous.keys()) ^ set(current.keys())
    changed_paths.update(path for path in previous.keys() & current.keys() if previous[path] != current[path])

    resolved: set[str] = set()
    for path in sorted(changed_paths):
        classified = classify_path(path, watch_roots)
        if classified is not None:
            resolved.add(classified)
    return sorted(resolved)


def choose_python() -> Path:
    if DEFAULT_PYTHON.exists():
        return DEFAULT_PYTHON
    return Path(sys.executable)


def run_once(runtime: IngestRunner, watch_roots: list[tuple[str, Path]]) -> int:
    targets = poll_once(watch_roots)
    if not targets:
        print("no relevant files found; running safe full ingest", flush=True)
        return runtime.run_once(["__full__:empty-scan"])
    return runtime.run_once(targets)


def run_polling(runtime: IngestRunner, watch_roots: list[tuple[str, Path]], poll_seconds: float) -> int:
    previous = snapshot_paths(watch_roots)
    print(f"polling mode active every {poll_seconds:.1f}s", flush=True)
    while True:
        time.sleep(poll_seconds)
        current = snapshot_paths(watch_roots)
        changed = diff_snapshots(previous, current, watch_roots)
        previous = current
        for source_name in changed:
            runtime.schedule(source_name)


def run_watchdog(
    runtime: IngestRunner,
    watch_roots: list[tuple[str, Path]],
    poll_seconds: float,
) -> int:
    if Observer is None:
        raise WatcherRuntimeError("watchdog is not available")

    observer = Observer()
    handler = DebouncedEventHandler(runtime, watch_roots)

    watched_any = False
    for _, root in watch_roots:
        if root.exists():
            observer.schedule(handler, str(root), recursive=True)
            print(f"watching {root}", flush=True)
            watched_any = True
        else:
            print(f"skipping missing watch root: {root}", flush=True)

    if not watched_any:
        print("no watch roots exist; falling back to polling", flush=True)
        return run_polling(runtime, watch_roots, poll_seconds)

    observer.start()
    stop_event = threading.Event()

    def _handle_signal(signum, _frame) -> None:
        print(f"received signal {signum}; shutting down", flush=True)
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _handle_signal)

    try:
        while not stop_event.is_set():
            time.sleep(0.5)
    finally:
        observer.stop()
        observer.join(timeout=5.0)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch vault and skills for ingest updates")
    parser.add_argument("--once", action="store_true", help="Run a single scan and exit")
    parser.add_argument("--poll-seconds", type=float, default=5.0, help="Polling interval fallback")
    parser.add_argument("--debounce-seconds", type=float, default=2.0, help="Debounce delay before ingest")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    watch_roots = determine_paths()
    runtime = IngestRunner(choose_python(), max(0.1, args.debounce_seconds))

    if args.once:
        return run_once(runtime, watch_roots)

    runtime.start()
    try:
        if Observer is not None:
            return run_watchdog(runtime, watch_roots, max(0.5, args.poll_seconds))
        print("watchdog not available, using polling fallback", flush=True)
        return run_polling(runtime, watch_roots, max(0.5, args.poll_seconds))
    finally:
        runtime.stop()


if __name__ == "__main__":
    raise SystemExit(main())
