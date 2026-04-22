# Integracoes Antigravity x Antaris

Esta nota agora funciona como indice curto. As fontes canonicas das integracoes ficaram distribuidas em diretorios proprios dentro de `.agent/`.

## Diretorios canonicos

- `.agent/README.md`
- `.agent/hermes/README.md`
- `.agent/obsidian/README.md`
- `.agent/brain/README.md`
- `.agent/gemini_mcp/README.md`
- `.agent/global_orchestrator/README.md`

## Entry points estaveis

- Vault Obsidian: `.agent/scripts/obsidian_*.py`
- Brain local: `.agent/brain/*.py`
- Gemini + MCP: `.agent/scripts/setup_gemini_mcp.py`, `.agent/scripts/test_gemini_auth.py`
- Hub unico: `.agent/scripts/antigravity_hub.py`

## Comandos principais

```bash
python3 .agent/scripts/antigravity_hub.py doctor
python3 .agent/scripts/antigravity_hub.py unify-hermes
python3 .agent/scripts/antigravity_hub.py install-launcher
python3 .agent/scripts/antigravity_hub.py generate-prefill
python3 .agent/scripts/antigravity_hub.py bootstrap
python3 .agent/scripts/antigravity_hub.py search "persona arquiteto" --limit 5
python3 .agent/scripts/antigravity_hub.py brain-query "persona arquiteto" --mode hybrid --limit 5
python3 .agent/scripts/antigravity_hub.py setup-mcp
python3 .agent/scripts/antigravity_hub.py gemini-test
antaris
```

## Observacoes da unificacao Hermes + Antaris

- O runtime continua sendo `Hermes`; `Antaris` e a identidade e a camada de contexto.
- `unify-hermes` agora tambem corrige configuracao de prefill, skills externos e symlink quebrado de `~/.local/bin/hermes`.
- A documentacao detalhada dessa camada vive em `.agent/hermes/README.md`.
