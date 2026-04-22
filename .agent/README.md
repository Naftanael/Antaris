# .agent

Mapa canonico da camada operacional do vault.

## Diretorios canonicos

- `.agent/hermes/` - unificacao entre Hermes runtime e identidade Antaris
- `.agent/obsidian/` - integracao do vault Obsidian e paths compartilhados
- `.agent/brain/` - infraestrutura local de indexacao e retrieval
- `.agent/gemini_mcp/` - integracao Gemini + MCP e template versionado
- `.agent/global_orchestrator/` - ponte entre o vault e o projeto `10 - Projetos/global-orchestrator`

## Diretorios de execucao

- `.agent/scripts/` - entrypoints e facades operacionais
- `.agent/memory/` - memoria persistente
- `.agent/rules/` - regras globais
- `.agent/agents/`, `.agent/skills/`, `.agent/workflows/` - Antigravity Kit

## Regra estrutural

Quando uma integracao crescer alem de um unico script, a fonte canônica deve ficar em um diretorio proprio dentro de `.agent/`. Os scripts em `.agent/scripts/` devem permanecer como entrypoints finos sempre que isso reduzir acoplamento.
