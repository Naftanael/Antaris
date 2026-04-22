# CODEBASE.md

## Overview
Este e o vault operacional do projeto **Antaris**, gerenciado pelo **Antigravity Kit**.
O repositorio combina conhecimento em Markdown, automacao local e integracoes para agentes.

## Estrutura do Projeto
- `.agent/`: Configuracoes, agentes, skills, workflows e integracoes locais.
- `.agent/hermes/`: unificacao entre runtime `Hermes` e identidade `Antaris`.
- `.agent/obsidian/`: integracao do vault e paths compartilhados.
- `.agent/brain/`: indexacao local, retrieval e `brain.db`.
- `.agent/gemini_mcp/`: configuracao Gemini + MCP.
- `.agent/global_orchestrator/`: ponte entre o vault e `10 - Projetos/global-orchestrator`.
- `.git/`: Repositório Git (exclusões locais configuradas em `.git/info/exclude`).
- `00 - Sistema/`: arquitetura, protocolos, personas e dashboards.
- `10 - Projetos/`: projetos ativos, incluindo `global-orchestrator` e `jarvis`.

## Camadas Arquiteturais
- Conhecimento: `00 - Sistema/`, `20 - Areas/`, `30 - Recursos/` e `99 - Inbox/`.
- Operacao: `.agent/` centraliza entrypoints, integracoes, memoria e retrieval.
- Execucao: `10 - Projetos/global-orchestrator/`, `10 - Projetos/jarvis/` e checkouts tecnicos correlatos.

## Subprojetos Ativos
- `global-orchestrator`: orquestrador Python com CLI, biblioteca, tracing e skills de ponte com o vault.
- `jarvis`: pipeline TypeScript para geracao deterministica de frontend, review automatizado e testes visuais.
- `hermes-webui`: interface Web do runtime Hermes que pode existir como checkout tecnico separado dentro do workspace.

## Artefatos Locais
- `.agent/brain/brain.db`: banco local de runtime para retrieval; nao e fonte canonica versionada.
- `.agent/vault-index.json`: indice gerado do vault.
- `.agent/context-manifest.md`: manifesto derivado para compressao de contexto.

## Entry Points
- `python3 .agent/scripts/antigravity_hub.py doctor`
- `python3 .agent/scripts/antigravity_hub.py unify-hermes`
- `python3 .agent/scripts/antigravity_hub.py generate-prefill`
- `python3 .agent/scripts/antigravity_hub.py launch-hermes`
- `antaris`

## Mudancas Recentes
- A unificacao `Hermes` + `Antaris` foi consolidada em `.agent/hermes/`.
- `unify-hermes` agora aplica `display.skin`, `prefill_messages_file` e `skills.external_dirs` no `~/.hermes/config.yaml`.
- A resolucao do runtime passou a suportar layout atual `~/.hermes/antaris-agent/hermes` e layout legado `~/.hermes/hermes-agent/venv/bin/hermes`.
- O setup agora repara automaticamente `~/.local/bin/hermes` quando existe link quebrado para o runtime legado.
- O `doctor` passou a validar configuracao de prefill e o link completo de skills/workflows externos.
- Foram adicionados testes de regressao para a unificacao em `10 - Projetos/global-orchestrator/tests/test_antaris_hermes_unification.py`.

## Dependências
- Python 3 para scripts do vault e do orquestrador.
- Runtime `Hermes` instalado fora do repositorio em `~/.hermes/`.

## Padrões de Desenvolvimento
- **IA**: Antigravity Kit v2
- **Workflow**: Socratic Gate + Implementation Planning
- **Validação**: Checklist automático via `.agent/scripts/checklist.py`

## Validacao Canonica
- `python3 .agent/scripts/antigravity_hub.py doctor --json`
- `python3 .agent/scripts/antigravity_hub.py unify-hermes --json`
- `python3 -m unittest discover -s tests -p 'test_*.py'` em `10 - Projetos/global-orchestrator/`
