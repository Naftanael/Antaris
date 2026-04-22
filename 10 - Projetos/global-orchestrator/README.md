# Global Agent Orchestrator

Um orquestrador de agentes modular e extensível construído em Python. Ele utiliza um sistema de descoberta automática de habilidades (skills) para expandir suas capacidades dinamicamente.

## 🌟 Funcionalidades

- **Descoberta Automática**: Adicione novos arquivos em `skills/` e eles serão carregados automaticamente.
- **Interface Dupla**: Use como uma ferramenta de linha de comando (CLI) ou como uma biblioteca Python.
- **Roteamento Inteligente**: Seleção automática da melhor habilidade para a tarefa.
- **Extensível**: Suporta funções locais, chamadas de API e delegação de LLM.
- **Integração com o vault Antaris**: Consulta bootstrap, busca em notas e brain local via `antaris_vault_skill`.
- **Integração com pipeline Jarvis**: Geração e validação de frontend via `jarvis_frontend_skill` (generate/review/test).
- **Cliente Gemini opcional**: Se `GOOGLE_GENAI_API_KEY` estiver configurado, o roteamento deixa de ser apenas heurístico.

## 🚀 Instalação

1. Clone o repositório.
2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Uso

### Como CLI

Inicie o chat interativo:
```bash
python main.py chat
```

Faça uma pergunta unica:
```bash
python main.py ask "buscar notas recentes do vault"
python main.py ask "jarvis gerar frontend dashboard de metricas"
```

Liste as habilidades instaladas:
```bash
python main.py list-skills
```

### Debug e Trace

Modo normal permanece limpo. Para observabilidade:

```bash
python main.py list-skills --debug
python main.py ask "listar arquivos" --trace
python main.py ask "listar arquivos" --debug --jsonl /tmp/orchestrator-events.jsonl
```

- `--debug`: eventos relevantes em console (`INFO+`, sem payload)
- `--trace`: eventos detalhados (`DEBUG+`, com payload)
- `--jsonl`: grava eventos estruturados em arquivo para análise posterior

### Como Biblioteca

```python
from api import GlobalAgent

agent = GlobalAgent()
response = agent.ask("Quanto é 15 * 25?")
print(response["result"])
```

Para biblioteca com tracing:

```python
from api import GlobalAgent

agent = GlobalAgent(debug=True, trace=True, jsonl_path="/tmp/orchestrator-events.jsonl")
response = agent.ask("listar arquivos")
```

### Replay por request_id

Replay mínimo disponível via módulo:

```bash
python -m core.debug.replay --file /tmp/orchestrator-events.jsonl --request-id <REQUEST_ID>
python -m core.debug.replay --file /tmp/orchestrator-events.jsonl --request-id <REQUEST_ID> --json
```

Isso retorna a história cronológica de eventos da requisição filtrada por `payload.request_id`.
Inclui eventos do orquestrador e da skill executada na mesma requisição.

## 🧩 Adicionando Novas Habilidades (Plugins)

Para adicionar uma nova habilidade, basta criar um arquivo `.py` dentro da pasta `skills/` seguindo este modelo:

```python
from core.base_skill import BaseSkill

class MyNewSkill(BaseSkill):
    @property
    def name(self):
        return "my_skill"

    @property
    def description(self):
        return "Faz algo incrível que o LLM deve saber."

    def execute(self, arguments):
        return "Resultado do processamento"
```

O orquestrador fará o resto!

## 🤖 Agent Information

Este projeto segue o padrão **llms.txt** para acessibilidade por agentes de IA.
- [llms.txt](./llms.txt): Mapa de alta fidelidade para LLMs.
- [docs/ARCHITECTURE-AI.md](./docs/ARCHITECTURE-AI.md): Documentação técnica para agentes.
- [docs/SKILL_GUIDE.md](./docs/SKILL_GUIDE.md): Guia de extensibilidade para IAs.

## Integração com Antaris

O repositório principal expõe um hub em `.agent/scripts/antigravity_hub.py`.
A skill `antaris_vault_skill` usa esse hub para:

- bootstrap de contexto do vault
- busca em `vault-index.json`
- relacionadas e notas recentes
- resumo de notas
- busca híbrida no `brain.db`
- health check das integrações

Variáveis opcionais:

- `GOOGLE_GENAI_API_KEY`
- `GOOGLE_GENAI_MODEL`

## Testes relevantes

Para validar a integracao atual do orquestrador com o vault e com a unificacao `Hermes` + `Antaris`:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Cobertura importante:
- `tests/test_orchestrator_vault_routing.py`
- `tests/test_orchestrator_jarvis_routing.py`
- `tests/test_antaris_hermes_unification.py`
