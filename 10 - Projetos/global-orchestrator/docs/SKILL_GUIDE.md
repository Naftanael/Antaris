# Guide: Creating New Skills (AI-Friendly)

Este guia explica como adicionar novas capacidades ao **Global Orchestrator**.

## 1. O Padrão de Plugin

O sistema utiliza reflexão (inspect) para encontrar classes. Qualquer classe que:
1. Resida em um arquivo `.py` dentro de `skills/`.
2. Herde de `BaseSkill`.
3. Não seja a própria `BaseSkill`.

Será carregada automaticamente no próximo boot do orquestrador.

## 2. Definindo a Identidade da Skill

O segredo para um roteamento perfeito está na propriedade `description`.

```python
@property
def description(self) -> str:
    return "Descrição rica em detalhes para o LLM."
```

### Dicas de Prompting para Descrição:
- Liste os **parâmetros** que a skill espera.
- Explique o **output** esperado.
- Adicione **casos de uso** (ex: "Use esta skill quando o usuário pedir X").

## 3. Tipos de Skills

### A. Skill Local (Python)
Executa código Python diretamente. Ideal para manipulação de arquivos ou lógica local.

### B. Skill de API (Externa)
Atua como um proxy para um serviço SaaS. Requer chaves de API no `.env`.

### C. Skill de Delegação (LLM)
Encaminha a tarefa para outro modelo ou com um prompt de sistema diferente.

## 4. Exemplo de Implementação

```python
from core.base_skill import BaseSkill

class SearchSkill(BaseSkill):
    @property
    def name(self):
        return "web_search"

    @property
    def description(self):
        return "Busca informações em tempo real na internet. Parâmetros: query (o termo de busca)."

    def execute(self, arguments):
        query = arguments.get("query")
        # Lógica de busca aqui
        return f"Resultados para {query}..."
```

## 5. Validação
Após criar sua skill, rode `python main.py list-skills` no terminal para confirmar que ela foi descoberta.
