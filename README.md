# Antaris

Antaris e um segundo cerebro operacional construido sobre Obsidian, com foco em agentes de IA, memoria persistente, recuperacao de contexto e automacao local.

Ele combina:
- uma base de conhecimento em Markdown organizada no vault
- personas e protocolos de PKM para estruturar conhecimento acionavel
- projetos tecnicos e documentacao para agentes
- um sistema autonomo de indexacao local (`brain.db`) para busca lexical e semantica

## Visao geral

Este repositorio funciona como:
- vault principal do projeto Antaris
- workspace de conhecimento para agentes e humano
- laboratorio de arquitetura de contexto para LLMs
- base de experimentacao para automacao, RAG e orquestracao de agentes

## Estrutura

```text
.
├── 00 - Sistema/              # arquitetura, protocolos, personas, templates, dashboards
├── 10 - Projetos/             # projetos ativos e subprojetos
├── 20 - Areas/                # areas continuas de responsabilidade
├── 30 - Recursos/             # referencias e materiais de apoio
├── 99 - Inbox/                # captura e triagem
├── copilot/                   # prompts e automacoes auxiliares
├── CODEBASE.md                # resumo estrutural do repositorio
└── README.md
```

## Principios do projeto

- conhecimento precisa ser reutilizavel, nao apenas armazenado
- contexto para LLM deve ser curado, comprimido e recuperavel
- notas devem gerar acao, nao apenas arquivo morto
- automacao deve reduzir friccao e economizar tokens
- o sistema deve evoluir com uso real

## Componentes principais

### 1. Vault PKM
O vault usa uma organizacao estilo PARA:
- `00 - Sistema`: a camada metacognitiva do projeto
- `10 - Projetos`: execucao e trabalho ativo
- `20 - Areas`: responsabilidades continuas
- `30 - Recursos`: conhecimento de referencia
- `99 - Inbox`: captura bruta

### 2. Personas e protocolo de integracao
Antaris usa personas especializadas para operar o conhecimento:
- Arquiteto
- Executor
- Engenheiro Tecnologico
- Sintetizador
- Orquestrador Multi-Agente

Documentos centrais:
- `00 - Sistema/Antaris-Architecture-For-AI.md`
- `00 - Sistema/Protocolo de Integração.md`
- `00 - Sistema/LLM Optimization Engine.md`
- `00 - Sistema/Self-Correction Log.md`

### 3. Global Agent Orchestrator
Dentro de `10 - Projetos/global-orchestrator/` ha um orquestrador modular em Python com descoberta automatica de skills.

Ver:
- `10 - Projetos/global-orchestrator/README.md`
- `10 - Projetos/global-orchestrator/docs/ARCHITECTURE-AI.md`
- `10 - Projetos/global-orchestrator/docs/SKILL_GUIDE.md`

### 4. Brain local para busca e memoria
Localmente, Antaris pode operar com um sistema autonomo de indexacao baseado em SQLite FTS5 + embeddings locais.

Capacidades do brain:
- ingestao incremental de notas, memoria e skills
- chunking por headings
- busca lexical, semantica e hibrida
- telemetria de acesso
- dashboard de estatisticas
- watcher para reindexacao automatica
- decay de relevancia ao longo do tempo

Observacao:
alguns componentes locais de agente/infra podem estar fora do versionamento principal dependendo da configuracao do repositorio.

## Casos de uso

- segundo cerebro para engenharia e pesquisa
- documentacao orientada a agentes de IA
- recuperacao de contexto para reduzir uso de tokens
- organizacao de workflows multiagente
- base de conhecimento operacional para projetos e experimentos

## Como usar

### Navegar pelo vault
Abra o repositorio como vault no Obsidian ou leia os arquivos Markdown diretamente.

### Pontos de entrada recomendados
- `CODEBASE.md`
- `00 - Sistema/Antaris-Architecture-For-AI.md`
- `00 - Sistema/Protocolo de Integração.md`
- `00 - Sistema/LLM Optimization Engine.md`
- `10 - Projetos/global-orchestrator/README.md`

### Trabalhar com agentes
O repositorio contem material voltado a agentes de IA, incluindo:
- protocolos de integracao
- templates de personas
- documentacao para orquestracao
- artefatos de contexto para LLMs

## Roadmap sugerido

- consolidar o brain local como componente versionado
- ampliar ingestao automatica de fontes externas
- criar dashboards e briefings recorrentes
- fortalecer a camada de RAG semantico
- integrar projetos ativos ao indice local

## Licenca

MIT. Veja [`LICENSE`](./LICENSE).

## Autor

Naftanael
