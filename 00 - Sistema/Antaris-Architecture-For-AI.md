# Arquitetura Antaris - Guia para LLMs e Agentes IA

Este documento descreve o fluxo arquitetural e estrutural do projeto `global-orchestrator` e `Antaris`. Ele deve ser consumido por sub-agentes instanciados via `delegate_task` para rápida compreensão do ecossistema.

## 🏗️ Topologia do Orquestrador Global

O sistema Antaris é baseado no **Global Agent Orchestrator**, construído em Python. Ele opera em um ciclo contínuo: **Classificação -> Seleção -> Execução**.

### Diretórios e Arquivos Críticos
- `main.py`: Ponto de entrada do sistema.
- `core/orchestrator.py`: Coração lógico. Contém o LLM que classifica intents e os roteia.
- `core/discovery.py`: Sistema de reflexão. Varre a pasta `skills/` e carrega as classes de forma autônoma.
- `skills/`: Diretório de habilidades modulares.

## 🧩 O Contrato Inquebrável: `BaseSkill`

Todo sub-agente designado a criar uma nova "habilidade" DEVE herdar da classe `BaseSkill` (normalmente importada de `core.base_skill`).

### Regras de Construção de uma Skill:
1. **Atributo `name`**: String única, sem espaços (ex: `minha_nova_skill`).
2. **Atributo `description`**: O MAIS IMPORTANTE. Deve ser extenso e detalhado. O orquestrador usa esta string diretamente no prompt de classificação para decidir quando chamar a skill.
3. **Método `execute(self, params: dict)`**: O ponto de entrada da execução. O parâmetro `params` vem diretamente do output JSON do LLM classificador.

## 🛡️ Protocolos de Segurança

- **NUNCA usar `eval()`, `exec()` ou `os.system` sem sanitização extrema.** 
- Se a skill exige execução dinâmica, utilizar Parseamento de AST (Abstract Syntax Tree) ou ambientes sandbox restritos (como implementado em `math_skill.py`).
- Prevenir State Leakage: Cada chamada de `execute()` deve ser idempotente ou lidar perfeitamente com seu próprio encerramento de conexões/arquivos.

> **Nota para Sub-Agentes:** Ao ler este arquivo, confirme com o orquestrador principal que a assimilação da topologia foi concluída antes de iniciar edições no código-fonte.