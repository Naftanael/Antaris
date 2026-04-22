import json
import os
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from uuid import uuid4

from core.debug.events import EventLevel
from core.debug.tracer import Tracer, ensure_tracer
from core.discovery import SkillDiscovery
from core.model_clients import GeminiModelClient, ModelClientError


@dataclass(frozen=True, slots=True)
class RequestTraceContext:
    request_id: str
    trace_id: str


class GlobalOrchestrator:
    def __init__(self, model_client: Any = None, tracer: Tracer | None = None):
        self.tracer = ensure_tracer(tracer)
        self.discovery = SkillDiscovery(tracer=self.tracer)
        self.skills = self.discovery.discover()
        self.history: List[Dict[str, str]] = []
        self.model_client = model_client or self._build_default_model_client()
        self.tracer.trace(
            "orchestrator.initialized",
            level=EventLevel.DEBUG,
            component="core.orchestrator",
            payload={"skills_count": len(self.skills)},
        )

    def _build_default_model_client(self) -> Any:
        api_key = os.environ.get("GOOGLE_GENAI_API_KEY")
        if not api_key:
            return None
        model_name = os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash")
        return GeminiModelClient(api_key=api_key, model=model_name)

    def _new_trace_context(
        self,
        *,
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> RequestTraceContext:
        return RequestTraceContext(
            request_id=request_id or str(uuid4()),
            trace_id=trace_id or str(uuid4()),
        )

    def _trace_event(
        self,
        event_name: str,
        *,
        context: RequestTraceContext,
        level: EventLevel = EventLevel.INFO,
        message: str | None = None,
        payload: Dict[str, Any] | None = None,
    ) -> None:
        merged_payload = dict(payload or {})
        merged_payload["request_id"] = context.request_id
        merged_payload["trace_id"] = context.trace_id
        self.tracer.trace(
            event_name,
            level=level,
            message=message,
            component="core.orchestrator",
            correlation_id=context.trace_id,
            payload=merged_payload,
        )

    def _get_system_prompt(self) -> str:
        skills_desc = "\n".join([
            f"- {skill.name}: {skill.description}" 
            for skill in self.skills.values()
        ])
        
        return f"""Você é um Orquestrador Global de Agentes.
Sua tarefa é analisar o pedido do usuário e decidir qual habilidade (skill) é a mais adequada.

HABILIDADES DISPONÍVEIS:
{skills_desc}
- fallback: Use esta se nenhuma das acima for adequada.

REGRAS:
1. Responda APENAS em formato JSON.
2. Formato: {{"skill": "nome_da_skill", "args": {{...}}, "reasoning": "por que escolheu esta skill"}}
3. Se escolher 'fallback', forneça uma resposta direta no campo 'response'.
"""

    def process_request(
        self,
        user_message: str,
        *,
        request_id: str | None = None,
        trace_id: str | None = None,
    ) -> Dict[str, Any]:
        """
        Recebe a mensagem do usuário, decide a skill e a executa.
        """
        context = self._new_trace_context(request_id=request_id, trace_id=trace_id)
        self.history.append({"role": "user", "content": user_message})
        self._trace_event(
            "request_received",
            context=context,
            level=EventLevel.INFO,
            payload={"user_message": user_message},
        )
        self._trace_event(
            "routing_started",
            context=context,
            level=EventLevel.DEBUG,
            payload={"model_client_enabled": self.model_client is not None},
        )
        
        # Aqui simulamos a chamada ao LLM. 
        # Em uma implementação real, usaríamos self.model_client.chat(...)
        decision = self._get_llm_decision(user_message, context=context)
        self._trace_event(
            "routing_decision",
            context=context,
            level=EventLevel.DEBUG,
            payload={
                "decision": decision,
                "selected_skill": decision.get("skill"),
            },
        )
        
        skill_name = decision.get("skill")
        args = decision.get("args", {})
        
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            self._trace_event(
                "skill_selected",
                context=context,
                level=EventLevel.INFO,
                message=f"Executando skill '{skill_name}'",
                payload={"skill": skill_name, "args": args},
            )
            if hasattr(skill, "set_trace_context"):
                skill.set_trace_context(
                    request_id=context.request_id,
                    trace_id=context.trace_id,
                )
            try:
                result = skill.execute(args)
            finally:
                if hasattr(skill, "clear_trace_context"):
                    skill.clear_trace_context()
            response = {"status": "success", "skill": skill_name, "result": result}
        else:
            response = {"status": "fallback", "content": decision.get("response", "Desculpe, não encontrei uma habilidade para isso.")}
            self._trace_event(
                "fallback_triggered",
                context=context,
                level=EventLevel.WARNING,
                payload={"decision": decision},
            )
            
        self.history.append({"role": "assistant", "content": str(response)})
        self._trace_event(
            "response_returned",
            context=context,
            level=EventLevel.INFO,
            payload={
                "status": response.get("status"),
                "skill": response.get("skill"),
                "response_kind": "fallback" if response.get("status") == "fallback" else "success",
            },
        )
        return response

    def _get_llm_decision(
        self,
        message: str,
        *,
        context: RequestTraceContext | None = None,
    ) -> Dict[str, Any]:
        """
        Lógica de decisão (mockada para este exemplo inicial ou integrada ao seu cliente).
        """
        if self.model_client is not None:
            try:
                response = self.model_client.complete(prompt=self._get_system_prompt(), message=message)
                return json.loads(response)
            except (json.JSONDecodeError, ModelClientError, KeyError, TypeError) as exc:
                if context is not None:
                    self._trace_event(
                        "routing_decision",
                        context=context,
                        level=EventLevel.WARNING,
                        message="Falha ao usar model_client; aplicando heurística local.",
                        payload={"error": str(exc), "decision_source": "heuristic_fallback"},
                    )
                else:
                    self.tracer.trace(
                        "routing_decision",
                        level=EventLevel.WARNING,
                        component="core.orchestrator",
                        message="Falha ao usar model_client; aplicando heurística local.",
                        payload={"error": str(exc), "decision_source": "heuristic_fallback"},
                    )
        return self._heuristic_decision(message)

    def _extract_quoted_or_tail(self, message: str, keyword: str) -> str:
        quoted = re.search(r'"([^"]+)"', message)
        if quoted:
            return quoted.group(1).strip()

        lowered = message.lower()
        idx = lowered.find(keyword)
        if idx < 0:
            return message.strip()
        return message[idx + len(keyword):].strip(" :,-")

    def _extract_query_after_keywords(self, message: str, keywords: list[str]) -> str:
        lowered = message.lower()
        for keyword in keywords:
            idx = lowered.find(keyword)
            if idx >= 0:
                candidate = message[idx + len(keyword):].strip(" :,-")
                if candidate:
                    return candidate
        return message.strip()

    def _heuristic_decision(self, message: str) -> Dict[str, Any]:
        msg = message.lower()
        if "soma" in msg or "calcula" in msg:
            return {
                "skill": "math_skill", 
                "args": {"expression": message},
                "reasoning": "O usuário solicitou um cálculo matemático."
            }
        elif any(
            term in msg
            for term in [
                "jarvis",
                "frontend",
                "interface",
                "pagina",
                "página",
                "tela",
                "layout",
                "componente",
            ]
        ) or re.search(r"\\bui\\b", msg):
            action = "pipeline"
            if any(term in msg for term in ["review", "revis", "avali"]):
                action = "review"
            elif any(term in msg for term in ["playwright", "axe", "snapshot", "teste visual", "testar", "teste"]):
                action = "test"
            elif any(term in msg for term in ["gerar", "generate", "criar", "build"]):
                action = "generate"

            prompt = self._extract_query_after_keywords(
                message,
                ["gerar", "generate", "criar", "build", "pagina", "página", "tela", "frontend", "interface"],
            )

            args: Dict[str, Any] = {"action": action}
            if action in {"generate", "pipeline"} and prompt:
                args["prompt"] = prompt
            if "baseline" in msg and any(term in msg for term in ["atualiz", "update", "renovar"]):
                args["update_baseline"] = True
            if "strict snapshot" in msg:
                args["strict_snapshots"] = True

            return {
                "skill": "jarvis_frontend_skill",
                "args": args,
                "reasoning": "O usuário está pedindo geração/validação de frontend no pipeline Jarvis.",
            }
        elif "listar" in msg or "arquivos" in msg:
            return {
                "skill": "shell_skill",
                "args": {"command": "ls -la"},
                "reasoning": "O usuário deseja visualizar os arquivos."
            }
        elif any(term in msg for term in ["vault", "obsidian", "nota", "notas", "pkm", "brain", "backlink", "wikilink", "contexto"]):
            if any(term in msg for term in ["bootstrap", "iniciar sess", "context manifest"]):
                return {
                    "skill": "antaris_vault_skill",
                    "args": {"action": "bootstrap"},
                    "reasoning": "O usuário pediu o carregamento inicial de contexto do vault."
                }
            if any(term in msg for term in ["recente", "recentes", "ultimas", "últimas"]):
                return {
                    "skill": "antaris_vault_skill",
                    "args": {"action": "recent", "days": 7, "limit": 5},
                    "reasoning": "O usuário pediu notas recentes do vault."
                }
            if any(term in msg for term in ["relacionad", "backlink", "wikilink"]):
                target = self._extract_quoted_or_tail(message, "relacion")
                return {
                    "skill": "antaris_vault_skill",
                    "args": {"action": "related", "target": target},
                    "reasoning": "O usuário pediu notas relacionadas."
                }
            if any(term in msg for term in ["resuma", "resumo", "summary"]):
                path = self._extract_quoted_or_tail(message, "resumo")
                return {
                    "skill": "antaris_vault_skill",
                    "args": {"action": "summary", "path": path},
                    "reasoning": "O usuário pediu o resumo de uma nota."
                }
            if any(term in msg for term in ["doctor", "health", "saude", "saúde", "integracao", "integração"]):
                return {
                    "skill": "antaris_vault_skill",
                    "args": {"action": "doctor"},
                    "reasoning": "O usuário quer verificar o estado das integrações."
                }
            if any(term in msg for term in ["brain", "semant", "hibrid"]):
                query = self._extract_query_after_keywords(
                    message,
                    ["brain", "semantica", "semântica", "hibrida", "híbrida", "buscar", "busque"],
                )
                return {
                    "skill": "antaris_vault_skill",
                    "args": {"action": "brain_search", "query": query, "limit": 5},
                    "reasoning": "O usuário quer buscar contexto no brain local."
                }
            query = self._extract_query_after_keywords(message, ["buscar", "busque", "procure", "pesquise"])
            return {
                "skill": "antaris_vault_skill",
                "args": {"action": "search", "query": query, "limit": 5},
                "reasoning": "O usuário quer consultar o vault Antaris."
            }
        
        return {
            "skill": "fallback",
            "response": "Olá! Sou seu orquestrador global. Como posso ajudar com minhas habilidades de matemática ou sistema?"
        }
