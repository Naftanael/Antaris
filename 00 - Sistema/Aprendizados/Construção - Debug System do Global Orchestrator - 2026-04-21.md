# Construção - Debug System do Global Orchestrator (2026-04-21)

## Contexto
Implementação ponta a ponta de observabilidade no projeto `10 - Projetos/global-orchestrator`, com foco em tracing estruturado, replay mínimo por `request_id` e testes curtos que comprovam o fluxo completo.

## O que foi implementado
- Modelo de evento estruturado (`DebugEvent`) com `level`, `timestamp`, `component`, `payload`, `correlation_id`.
- Abstração de tracer com `Tracer`, `NullTracer`, `SinkTracer`, `CompositeTracer`.
- Sinks de saída:
  - `ConsoleSink` (modo debug/trace)
  - `JSONLSink` (persistência para auditoria e replay)
- Builder de runtime (`build_runtime_tracer`) para ligar/desligar observabilidade por flags.
- Instrumentação no orquestrador:
  - início e fim de requisição
  - início de roteamento e decisão
  - seleção de skill
  - fallback
- Instrumentação nas skills (`math_skill`, `shell_skill`) para eventos de início/fim/erro.
- Propagação de `request_id` e `trace_id` para eventos de skill, permitindo replay completo por requisição.
- Replay mínimo em `core.debug.replay` com:
  - função `replay_by_request_id(path, request_id)`
  - CLI `python -m core.debug.replay --file ... --request-id ... [--json]`

## Aprendizados técnicos relevantes
- `NullTracer` simplifica operação em modo normal e evita condicionais espalhadas no código.
- `payload.request_id` é o identificador mais útil para reconstruir história operacional de uma requisição.
- Sem propagação do contexto para skill, replay fica incompleto (só mostra eventos do orquestrador).
- `pytest` pode falhar com import relativo dependendo de como é invocado; `tests/conftest.py` estabiliza `sys.path`.
- Import antecipado de `replay` em `core.debug.__init__` pode causar warning em `python -m`; lazy import resolve sem complexidade extra.

## Estratégia de testes que funcionou
Cobertura focada em comportamento observável (sem infraestrutura pesada):
- evento no início/fim de requisição
- discovery emitindo evento
- execução de skill emitindo evento
- erro de skill emitindo evento de erro
- `NullTracer` sem quebrar execução
- escrita JSONL válida
- replay cronológico por `request_id`

## Comandos úteis (referência rápida)
```bash
python main.py ask "listar arquivos" --debug
python main.py ask "listar arquivos" --trace
python main.py ask "listar arquivos" --debug --jsonl /tmp/orchestrator-events.jsonl
python -m core.debug.replay --file /tmp/orchestrator-events.jsonl --request-id <REQUEST_ID>
python -m core.debug.replay --file /tmp/orchestrator-events.jsonl --request-id <REQUEST_ID> --json
```

## Limitações atuais
- Replay simples (arquivo JSONL único; sem merge multi-fonte).
- Sem rotação de logs nativa.
- Ordenação por timestamp textual (suficiente para o estado atual).

## Próximos passos sugeridos
1. Adicionar filtros de replay por `trace_id`, `component` e intervalo de tempo.
2. Adicionar redaction padrão de payload para campos sensíveis.
3. Incluir smoke test de CLI (`--debug/--trace/--jsonl`) no pipeline.

## Referências
- `10 - Projetos/global-orchestrator/README.md`
- `10 - Projetos/global-orchestrator/core/debug/`
- `10 - Projetos/global-orchestrator/tests/test_debug_system.py`
