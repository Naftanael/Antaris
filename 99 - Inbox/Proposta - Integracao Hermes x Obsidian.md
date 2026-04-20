---
tipo: proposta
status: draft
autor: Claude (Hermes Agent)
criado: 2026-04-20
tags: [pkm, integracao, contexto, tokens, arquitetura]
---

# Proposta: Integracao Hermes Agent x Vault Obsidian

## Contexto

Vault atual: 197 notas, ~26k linhas de markdown
Distribuicao:
- 00 - Sistema: 20 notas, 634 linhas (arquitetura, protocolos)
- 10 - Projetos: 3 notas, 200 linhas
- 30 - Recursos: 162 notas, 25.079 linhas (~200k tokens) <-- gargalo
- .agent: workflows, agents, skills (Antigravity Kit v2)

Problema: Carregar o vault inteiro custa muito. A skill atual `obsidian` so faz grep/find,
e cada pergunta reabre arquivos ja lidos. Sem memoria persistente do que foi lido,
sem priorizacao por relevancia, sem cache.

## Objetivos

1. Reduzir tokens gastos em 60-80% em sessoes repetidas
2. Carregar so o contexto relevante (nao o vault inteiro)
3. Manter sincronia bidirecional (eu escrevo, voce ve; voce edita, eu vejo)
4. Permitir que eu atualize meu proprio contexto entre sessoes

## Arquitetura Proposta - 4 camadas

### Camada 1: Indice de Vault (static, barato)

Arquivo: `.agent/vault-index.json` (gerado por script, atualizado on-demand)

Formato:
  {
    "note_path": "00 - Sistema/LLM Optimization Engine.md",
    "title": "LLM Optimization Engine",
    "tags": ["llm", "otimizacao"],
    "size_lines": 45,
    "updated": "2026-04-15",
    "summary_30w": "Engine para otimizar prompts e reduzir tokens em chamadas LLM",
    "links_out": ["[[Protocolo de Integracao]]", "[[CODEBASE]]"],
    "links_in": ["[[Antaris-Architecture-For-AI]]"]
  }

Custo: carregar o indice inteiro = ~5k tokens (vs 200k do vault completo).
Me da visao global sem ler nenhuma nota.

### Camada 2: Context Manifest (dinamico, por sessao)

Arquivo: `.agent/context-manifest.md`

Lista curada das 5-10 notas criticas que eu SEMPRE devo ter em mente:
- Antaris-Architecture-For-AI.md
- Protocolo de Integracao.md
- CODEBASE.md
- Nota do projeto ativo atual

Voce mantem essa lista. A skill obsidian vai carregar automaticamente
esse manifest no inicio de toda sessao (~2k tokens).

### Camada 3: Memoria Persistente do Agente

Pasta: `.agent/memory/`
- `session-log.md`: o que eu fiz em cada sessao (append-only)
- `user-preferences.md`: o que aprendi sobre voce (sincronizado com minha memory tool)
- `project-state.md`: estado atual de cada projeto em "10 - Projetos"
- `lessons-learned.md`: erros, correcoes, patterns que descobri

Eu escrevo essa pasta ao final de cada sessao. Na proxima sessao, leio primeiro.
Substitui o "session_search" caro por uma memoria curada por mim mesmo.

### Camada 4: Retrieval sob demanda

Scripts em `.agent/scripts/`:
- `obsidian_search.py`: busca semantica (grep + ranking por tags/titulo/links)
- `obsidian_related.py`: dado uma nota, retorna backlinks e notas relacionadas
- `obsidian_recent.py`: notas modificadas nos ultimos N dias
- `obsidian_summary.py`: resume uma nota longa em N tokens

So carrego o conteudo completo quando preciso editar ou raciocinar sobre a nota.

## Fluxo de uma sessao tipica

1. Voce: "Claude, atualiza o estado do projeto X"
2. Eu: leio `.agent/memory/project-state.md` (300 tokens) + `10 - Projetos/X.md` (500 tokens)
   em vez de escanear o vault inteiro (200k tokens)
3. Edito a nota, atualizo project-state.md, escrevo entry em session-log.md
4. Proxima sessao: continuo de onde parei, sem voce precisar me explicar nada

## Wikilinks como protocolo de navegacao

Uso `[[Nome da Nota]]` como "ponteiros" em vez de paths completos.
A skill resolve wikilink -> path. Beneficios:
- Economizo tokens (nome curto em vez de path)
- Respeito a convencao do Obsidian
- Funciona mesmo se a nota for movida (desde que o nome seja unico)

## Upgrades na skill `obsidian`

Adicionar comandos:
- `obsidian_bootstrap`: roda no inicio da sessao, carrega manifest + memory
- `obsidian_checkpoint`: roda no fim da sessao, atualiza memory
- `obsidian_index`: regenera vault-index.json
- `obsidian_relevant(query)`: retorna top-5 notas relevantes a uma query

## Plano de implementacao

Fase 1 (30 min): criar scripts de indexacao e memoria
Fase 2 (15 min): escrever .agent/context-manifest.md inicial
Fase 3 (15 min): atualizar a skill obsidian com os novos comandos
Fase 4 (validacao): rodar uma sessao de teste e medir tokens

## Economia estimada

Cenario | Antes | Depois | Ganho
---|---|---|---
Sessao curta (consulta) | 15k tokens | 3k tokens | 80%
Sessao media (edicao) | 40k tokens | 10k tokens | 75%
Sessao longa (projeto) | 100k tokens | 25k tokens | 75%

## Decisoes que preciso de voce

1. Voce aprova criar `.agent/memory/` para eu escrever estado entre sessoes?
2. Quer o index regenerado automaticamente (em cada checkpoint) ou manual?
3. Devo indexar a pasta `30 - Recursos/Langflow` (maior parte dos 200k tokens)
   ou ignorar ate voce precisar dela?
4. Comeco pela Fase 1 agora ou aprova o plano inteiro primeiro?

## Links relacionados

- [[Antaris-Architecture-For-AI]]
- [[Protocolo de Integracao]]
- [[LLM Optimization Engine]]
- [[CODEBASE]]
