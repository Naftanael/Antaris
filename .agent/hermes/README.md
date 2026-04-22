# Hermes + Antaris

Diretorio canonico da unificacao entre o runtime `Hermes` e a camada operacional `Antaris`.

## O que fica aqui

- `hermes_unification.py`: logica da unificacao local
- `generate_prefill.py`: gerador do contexto auto-injetado no inicio de sessao
- `antaris-skin.yaml`: identidade visual aplicada no `~/.hermes/skins/`
- `ANTARIS_SOUL.md`: identidade textual aplicada no `~/.hermes/SOUL.md`
- `antaris-launcher.sh`: template do comando `~/.local/bin/antaris`

## Regra arquitetural

- `Hermes` continua como runtime, CLI/TUI, tool execution e configuracao local.
- `Antaris` continua como identidade, memoria operacional, vault e camada de contexto.
- Nao renomear ou forkar o upstream do `hermes-agent` para expressar essa unificacao.

## Fluxo operacional

### Instalar ou reaplicar a unificacao

```bash
python3 .agent/scripts/antigravity_hub.py unify-hermes
```

Aplica: skin, SOUL, launcher, prefill de contexto e config de skin.

### Reinstalar somente o launcher

```bash
python3 .agent/scripts/antigravity_hub.py install-launcher
```

### Regenerar o prefill de contexto

```bash
python3 .agent/scripts/antigravity_hub.py generate-prefill
```

O prefill e um JSONL com ~700 tokens que o Hermes injeta automaticamente ao inicio de cada sessao. Contem: identidade, estado dos projetos, aprendizados e ferramentas disponiveis.

### Auditar estado

```bash
python3 .agent/scripts/antigravity_hub.py doctor
```

### Iniciar

```bash
antaris
```

Ou:

```bash
python3 .agent/scripts/antigravity_hub.py launch-hermes
```

## Arquivos aplicados fora do vault

- `~/.hermes/skins/antaris.yaml`
- `~/.hermes/SOUL.md`
- `~/.hermes/antaris_prefill.jsonl`
- `~/.hermes/config.yaml` (display.skin, prefill_messages_file, skills.external_dirs)
- `~/.local/bin/antaris`

## Integracao de Skills

Os 39 skills do Antigravity Kit sao expostos ao Hermes via `skills.external_dirs` no config.yaml, apontando para:
- `.agent/skills/` (39 skills de desenvolvimento)
- `.agent/workflows/` (11 workflows de slash commands)

Isso evita duplicacao — o Hermes descobre os skills direto do vault.

Alem disso, o skill `antaris-context` fornece acesso nativo ao bootstrap, brain search e session management.

## Papel do antigravity_hub

`antigravity_hub.py` permanece como entrypoint unico do vault, mas a fonte da unificacao Hermes + Antaris vive aqui neste diretorio.
