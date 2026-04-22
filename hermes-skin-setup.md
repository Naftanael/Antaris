# Hermes Skin Setup

## Objetivo

Esta nota documenta o setup operacional da identidade `Antaris` sobre o runtime `Hermes`.

O objetivo nao e renomear o upstream, e sim aplicar:
- skin visual
- identidade textual
- prefill de contexto
- launcher local
- configuracao de skills externos

## Comando principal

```bash
python3 .agent/scripts/antigravity_hub.py unify-hermes
```

Esse comando faz:
- instala `~/.hermes/skins/antaris.yaml`
- aplica `~/.hermes/SOUL.md`
- gera `~/.hermes/antaris_prefill.jsonl`
- instala `~/.local/bin/antaris`
- garante `display.skin: antaris`
- garante `prefill_messages_file: ~/.hermes/antaris_prefill.jsonl`
- garante `skills.external_dirs` com `.agent/skills/` e `.agent/workflows/`
- repara `~/.local/bin/hermes` se houver link quebrado para um layout legado

## Layouts de runtime suportados

O bootstrap local tenta resolver o executavel `hermes` nesta ordem:
- `which hermes`
- `~/.local/bin/hermes`
- `~/.hermes/antaris-agent/hermes`
- `~/.hermes/hermes-agent/venv/bin/hermes`

Isso cobre migracoes do layout antigo para o layout atual sem exigir edicao manual do launcher.

## Auditoria

```bash
python3 .agent/scripts/antigravity_hub.py doctor
```

Os checks mais importantes dessa integracao sao:
- `hermes-binary`
- `hermes-active-skin`
- `hermes-soul`
- `hermes-prefill`
- `hermes-prefill-config`
- `hermes-external-skills`
- `antaris-launcher`

## Troubleshooting

### `hermes-binary` em `warn`

Rode:

```bash
python3 .agent/scripts/antigravity_hub.py unify-hermes
```

Se o runtime existir em `~/.hermes/antaris-agent/hermes` ou no layout legado, o symlink local sera reparado.

### Sessao abre sem contexto inicial

Verifique:

```bash
python3 .agent/scripts/antigravity_hub.py doctor --json
```

O item `hermes-prefill-config` precisa estar em `ok`.

### Skills do vault nao aparecem no Hermes

O item `hermes-external-skills` precisa estar em `ok`.
Ele valida que `skills.external_dirs` aponta para:
- `.agent/skills/`
- `.agent/workflows/`

## Validacao executada

Comandos usados na validacao de regressao:

```bash
python3 .agent/scripts/antigravity_hub.py unify-hermes --json
python3 .agent/scripts/antigravity_hub.py doctor --json
cd "10 - Projetos/global-orchestrator"
python3 -m unittest discover -s tests -p 'test_*.py'
```
