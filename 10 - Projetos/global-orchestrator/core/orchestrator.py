import json
from typing import List, Dict, Any, Optional
from core.discovery import SkillDiscovery

class GlobalOrchestrator:
    def __init__(self, model_client: Any = None):
        self.discovery = SkillDiscovery()
        self.skills = self.discovery.discover()
        self.history: List[Dict[str, str]] = []
        self.model_client = model_client

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

    def process_request(self, user_message: str) -> Dict[str, Any]:
        """
        Recebe a mensagem do usuário, decide a skill e a executa.
        """
        self.history.append({"role": "user", "content": user_message})
        
        # Aqui simulamos a chamada ao LLM. 
        # Em uma implementação real, usaríamos self.model_client.chat(...)
        decision = self._get_llm_decision(user_message)
        
        skill_name = decision.get("skill")
        args = decision.get("args", {})
        
        if skill_name in self.skills:
            print(f"🤖 Orquestrador: Executando skill '{skill_name}'...")
            result = self.skills[skill_name].execute(args)
            response = {"status": "success", "skill": skill_name, "result": result}
        else:
            response = {"status": "fallback", "content": decision.get("response", "Desculpe, não encontrei uma habilidade para isso.")}
            
        self.history.append({"role": "assistant", "content": str(response)})
        return response

    def _get_llm_decision(self, message: str) -> Dict[str, Any]:
        """
        Lógica de decisão (mockada para este exemplo inicial ou integrada ao seu cliente).
        """
        # Se tivéssemos o cliente real:
        # response = self.model_client.complete(prompt=self._get_system_prompt(), message=message)
        # return json.loads(response)
        
        # Mocking básico para demonstração
        msg = message.lower()
        if "soma" in msg or "calcula" in msg:
            return {
                "skill": "math_skill", 
                "args": {"expression": message},
                "reasoning": "O usuário solicitou um cálculo matemático."
            }
        elif "listar" in msg or "arquivos" in msg:
            return {
                "skill": "shell_skill",
                "args": {"command": "ls -la"},
                "reasoning": "O usuário deseja visualizar os arquivos."
            }
        
        return {
            "skill": "fallback",
            "response": "Olá! Sou seu orquestrador global. Como posso ajudar com minhas habilidades de matemática ou sistema?"
        }
