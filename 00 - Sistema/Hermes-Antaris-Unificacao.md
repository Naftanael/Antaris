---
tipo: arquitetura
status: implemented
atualizado: 2026-04-22
tags: [antaris, hermes, unificacao, runtime, identidade]
---

# Hermes + Antaris - Indice de Unificacao

Esta nota deixou de ser a fonte canonica da unificacao.

Agora a fonte versionada e centralizada em:

- `.agent/hermes/README.md`
- `.agent/hermes/hermes_unification.py`
- `.agent/hermes/antaris-skin.yaml`
- `.agent/hermes/ANTARIS_SOUL.md`
- `.agent/hermes/antaris-launcher.sh`

## Regra atual

- `Hermes` continua sendo o runtime
- `Antaris` continua sendo a identidade e a camada de contexto
- `antigravity_hub.py` continua sendo o entrypoint operacional
- `.agent/hermes/` e o diretorio canonico da unificacao

## Mudancas documentadas em 2026-04-22

- `unify-hermes` agora aplica configuracao completa do runtime:
  `display.skin`, `prefill_messages_file` e `skills.external_dirs`.
- A resolucao do binario `hermes` passou a aceitar o layout atual `~/.hermes/antaris-agent/hermes` e o layout legado `~/.hermes/hermes-agent/venv/bin/hermes`.
- O setup passou a reparar automaticamente `~/.local/bin/hermes` quando encontra um symlink quebrado.
- O `doctor` passou a validar `hermes-prefill-config` e a integridade completa de `skills.external_dirs`.
- O gerador de prefill passou a respeitar `HERMES_HOME`.
- Foram adicionados testes de regressao para a unificacao em `10 - Projetos/global-orchestrator/tests/test_antaris_hermes_unification.py`.

## Comandos

```bash
python3 .agent/scripts/antigravity_hub.py unify-hermes
python3 .agent/scripts/antigravity_hub.py install-launcher
python3 .agent/scripts/antigravity_hub.py generate-prefill
python3 .agent/scripts/antigravity_hub.py doctor
antaris
```

## Validacao

Comandos usados para validar a mudanca:

```bash
python3 .agent/scripts/antigravity_hub.py unify-hermes --json
python3 .agent/scripts/antigravity_hub.py doctor --json
cd "10 - Projetos/global-orchestrator"
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Links do vault

- `.agent/hermes/README.md`
- `hermes-skin-setup.md`
- [[Antaris-Architecture-For-AI]]
- [[Protocolo de Integração]]
- [[LLM Optimization Engine]]
- [[CODEBASE]]
