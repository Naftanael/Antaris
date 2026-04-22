from __future__ import annotations

import unittest

from core.debug.tracer import NullTracer
from core.orchestrator import GlobalOrchestrator


class OrchestratorJarvisRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.orchestrator = GlobalOrchestrator(model_client=None, tracer=NullTracer())

    def test_routes_frontend_generation_requests_to_jarvis_skill(self) -> None:
        decision = self.orchestrator._heuristic_decision(
            "jarvis gerar frontend dashboard de metricas para agentes"
        )

        self.assertEqual(decision["skill"], "jarvis_frontend_skill")
        self.assertEqual(decision["args"]["action"], "generate")
        self.assertIn("dashboard", decision["args"]["prompt"].lower())

    def test_routes_review_requests_to_jarvis_skill(self) -> None:
        decision = self.orchestrator._heuristic_decision(
            "fazer review da pagina frontend do jarvis"
        )

        self.assertEqual(decision["skill"], "jarvis_frontend_skill")
        self.assertEqual(decision["args"]["action"], "review")

    def test_routes_visual_test_requests_to_jarvis_skill(self) -> None:
        decision = self.orchestrator._heuristic_decision(
            "rodar playwright e axe na tela do jarvis"
        )

        self.assertEqual(decision["skill"], "jarvis_frontend_skill")
        self.assertEqual(decision["args"]["action"], "test")


if __name__ == "__main__":
    unittest.main()
