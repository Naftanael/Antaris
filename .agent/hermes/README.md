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

Aplica:
- skin `antaris`
- `SOUL.md`
- launcher `~/.local/bin/antaris`
- prefill de contexto
- `display.skin`, `prefill_messages_file` e `skills.external_dirs` no `~/.hermes/config.yaml`
- reparo automatico do link `~/.local/bin/hermes` quando ele aponta para um runtime legado inexistente

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

O `doctor` agora valida:
- binario `hermes` resolvido
- skin `antaris` instalada e ativa
- `SOUL.md` aplicada
- `prefill_messages_file` configurado
- `skills.external_dirs` apontando para `.agent/skills/` e `.agent/workflows/`

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
- `~/.local/bin/hermes` (symlink para o runtime real quando necessario)
- `~/.local/bin/antaris`

## Integracao de Skills

Os 39 skills do Antigravity Kit sao expostos ao Hermes via `skills.external_dirs` no config.yaml, apontando para:
- `.agent/skills/` (39 skills de desenvolvimento)
- `.agent/workflows/` (11 workflows de slash commands)

Isso evita duplicacao — o Hermes descobre os skills direto do vault.

Alem disso, o skill `antaris-context` fornece acesso nativo ao bootstrap, brain search e session management.

## Resolucao do runtime

O runtime continua sendo `Hermes`, mas o bootstrap local agora aceita mais de um layout de instalacao:
- `which hermes`
- `~/.local/bin/hermes`
- `~/.hermes/antaris-agent/hermes`
- `~/.hermes/hermes-agent/venv/bin/hermes`

Se o link `~/.local/bin/hermes` existir, mas estiver quebrado por migracao do layout legado para o atual, `unify-hermes` repara esse symlink automaticamente.

## Prefill e compatibilidade

`generate_prefill.py` continua gerando `~/.hermes/antaris_prefill.jsonl`, mas agora respeita `HERMES_HOME` quando esse ambiente e definido.

Isso mantem o comportamento previsivel em perfis alternativos do Hermes sem fixar o runtime apenas em `~/.hermes`.

## Testes e validacao

Testes relevantes:
- `10 - Projetos/global-orchestrator/tests/test_antaris_hermes_unification.py`
- `10 - Projetos/global-orchestrator/tests/test_orchestrator_vault_routing.py`
- `10 - Projetos/global-orchestrator/tests/test_orchestrator_jarvis_routing.py`

Comando de regressao:

```bash
cd "10 - Projetos/global-orchestrator"
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Papel do antigravity_hub

`antigravity_hub.py` permanece como entrypoint unico do vault, mas a fonte da unificacao Hermes + Antaris vive aqui neste diretorio.
