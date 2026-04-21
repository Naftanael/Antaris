from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.debug.events import EventLevel
from core.debug.replay import replay_by_request_id
from core.debug.sinks import JSONLSink
from core.debug.tracer import NullTracer, SinkTracer
from core.discovery import SkillDiscovery
from core.orchestrator import GlobalOrchestrator


class MemorySink:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def write(self, event) -> None:
        self.events.append(event.to_dict())

    def flush(self) -> None:
        return None

    def close(self) -> None:
        return None


class DebugSystemTests(unittest.TestCase):
    def test_process_request_emits_start_and_end_events(self) -> None:
        sink = MemorySink()
        tracer = SinkTracer([sink])
        orchestrator = GlobalOrchestrator(model_client=None, tracer=tracer)

        request_id = "req-test-001"
        response = orchestrator.process_request("listar arquivos", request_id=request_id)
        self.assertEqual(response["status"], "success")

        names = [event["name"] for event in sink.events]
        self.assertIn("request_received", names)
        self.assertIn("response_returned", names)

        request_events = [
            event for event in sink.events if event.get("payload", {}).get("request_id") == request_id
        ]
        self.assertGreaterEqual(len(request_events), 2)

    def test_discovery_emits_skill_discovered_event(self) -> None:
        sink = MemorySink()
        tracer = SinkTracer([sink])
        discovery = SkillDiscovery(tracer=tracer)
        skills = discovery.discover()

        self.assertIn("math_skill", skills)
        names = [event["name"] for event in sink.events]
        self.assertIn("skill_discovered", names)

    def test_skill_execution_emits_events(self) -> None:
        sink = MemorySink()
        tracer = SinkTracer([sink])
        orchestrator = GlobalOrchestrator(model_client=None, tracer=tracer)

        request_id = "req-skill-events-001"
        response = orchestrator.process_request("listar arquivos", request_id=request_id)
        self.assertEqual(response["skill"], "shell_skill")

        names = [event["name"] for event in sink.events]
        self.assertIn("skill_execution_started", names)
        self.assertIn("skill_execution_finished", names)
        request_events = [
            event for event in sink.events if event.get("payload", {}).get("request_id") == request_id
        ]
        request_event_names = [event["name"] for event in request_events]
        self.assertIn("skill_execution_started", request_event_names)
        self.assertIn("skill_execution_finished", request_event_names)

    def test_skill_error_emits_error_event(self) -> None:
        sink = MemorySink()
        tracer = SinkTracer([sink])
        discovery = SkillDiscovery(tracer=tracer)
        skills = discovery.discover()

        result = skills["math_skill"].execute({"expression": "calcula 2+2"})
        self.assertIn("Erro na execução rápida", result)

        error_events = [event for event in sink.events if event["name"] == "skill_execution_error"]
        self.assertGreaterEqual(len(error_events), 1)
        self.assertEqual(error_events[-1]["level"], EventLevel.ERROR.value)

    def test_null_tracer_does_not_break_execution(self) -> None:
        orchestrator = GlobalOrchestrator(model_client=None, tracer=NullTracer())
        response = orchestrator.process_request("listar arquivos")
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["skill"], "shell_skill")

    def test_jsonl_sink_writes_valid_json_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "events.jsonl"
            sink = JSONLSink(path)
            tracer = SinkTracer([sink])
            tracer.trace(
                "unit_test_event",
                level=EventLevel.INFO,
                payload={"request_id": "req-jsonl-1"},
            )
            sink.flush()

            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            payload = json.loads(lines[0])
            self.assertEqual(payload["name"], "unit_test_event")
            self.assertEqual(payload["payload"]["request_id"], "req-jsonl-1")

    def test_replay_by_request_id_returns_chronological_story(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "trace.jsonl"
            sink = JSONLSink(path)
            memory = MemorySink()
            tracer = SinkTracer([memory, sink])
            orchestrator = GlobalOrchestrator(model_client=None, tracer=tracer)

            request_id = "req-replay-001"
            orchestrator.process_request("listar arquivos", request_id=request_id, trace_id="trace-replay-001")
            sink.flush()

            replay_events = replay_by_request_id(path, request_id)
            self.assertGreaterEqual(len(replay_events), 4)
            replay_names = [event["name"] for event in replay_events]
            self.assertIn("skill_execution_started", replay_names)
            self.assertIn("skill_execution_finished", replay_names)
            self.assertEqual(replay_events[0]["name"], "request_received")
            self.assertEqual(replay_events[-1]["name"], "response_returned")


if __name__ == "__main__":
    unittest.main()
