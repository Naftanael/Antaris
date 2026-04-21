from __future__ import annotations

import unittest

from core.debug.tracer import NullTracer
from core.orchestrator import GlobalOrchestrator


class OrchestratorVaultRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.orchestrator = GlobalOrchestrator(model_client=None, tracer=NullTracer())

    def test_routes_bootstrap_requests_to_vault_skill(self) -> None:
        decision = self.orchestrator._heuristic_decision("iniciar sessao do vault com context manifest")

        self.assertEqual(decision["skill"], "antaris_vault_skill")
        self.assertEqual(decision["args"]["action"], "bootstrap")

    def test_routes_recent_notes_requests_to_vault_skill(self) -> None:
        decision = self.orchestrator._heuristic_decision("mostrar notas recentes do vault")

        self.assertEqual(decision["skill"], "antaris_vault_skill")
        self.assertEqual(decision["args"]["action"], "recent")
        self.assertEqual(decision["args"]["days"], 7)
        self.assertEqual(decision["args"]["limit"], 5)

    def test_routes_related_notes_with_quoted_target(self) -> None:
        decision = self.orchestrator._heuristic_decision('quero notas relacionadas "Projeto Hermes" no vault')

        self.assertEqual(decision["skill"], "antaris_vault_skill")
        self.assertEqual(decision["args"]["action"], "related")
        self.assertEqual(decision["args"]["target"], "Projeto Hermes")

    def test_routes_summary_requests_with_quoted_path(self) -> None:
        decision = self.orchestrator._heuristic_decision('resuma "00 - Sistema/Antaris-Architecture-For-AI.md" nas notas')

        self.assertEqual(decision["skill"], "antaris_vault_skill")
        self.assertEqual(decision["args"]["action"], "summary")
        self.assertEqual(decision["args"]["path"], "00 - Sistema/Antaris-Architecture-For-AI.md")

    def test_routes_doctor_requests_to_vault_skill(self) -> None:
        decision = self.orchestrator._heuristic_decision("rode doctor de integracao do vault")

        self.assertEqual(decision["skill"], "antaris_vault_skill")
        self.assertEqual(decision["args"]["action"], "doctor")

    def test_routes_brain_search_with_query_extraction(self) -> None:
        decision = self.orchestrator._heuristic_decision("buscar no brain persona arquiteto")

        self.assertEqual(decision["skill"], "antaris_vault_skill")
        self.assertEqual(decision["args"]["action"], "brain_search")
        self.assertEqual(decision["args"]["query"], "persona arquiteto")
        self.assertEqual(decision["args"]["limit"], 5)

    def test_routes_default_vault_search_when_no_other_action_matches(self) -> None:
        decision = self.orchestrator._heuristic_decision("vault buscar persona arquiteto")

        self.assertEqual(decision["skill"], "antaris_vault_skill")
        self.assertEqual(decision["args"]["action"], "search")
        self.assertEqual(decision["args"]["query"], "persona arquiteto")
        self.assertEqual(decision["args"]["limit"], 5)


if __name__ == "__main__":
    unittest.main()
