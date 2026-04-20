# Global Agent Orchestrator

Um orquestrador de agentes modular e extensível construído em Python. Ele utiliza um sistema de descoberta automática de habilidades (skills) para expandir suas capacidades dinamicamente.

## 🌟 Funcionalidades

- **Descoberta Automática**: Adicione novos arquivos em `skills/` e eles serão carregados automaticamente.
- **Interface Dupla**: Use como uma ferramenta de linha de comando (CLI) ou como uma biblioteca Python.
- **Roteamento Inteligente**: Seleção automática da melhor habilidade para a tarefa.
- **Extensível**: Suporta funções locais, chamadas de API e delegação de LLM.

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

Liste as habilidades instaladas:
```bash
python main.py list-skills
```

### Como Biblioteca

```python
from api import GlobalAgent

agent = GlobalAgent()
response = agent.ask("Quanto é 15 * 25?")
print(response["result"])
```

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
