# Gemini + MCP Integration

Diretorio canonico da integracao Gemini + MCP do vault Antaris.

## O que fica aqui

- `mcp_config.template.json` - template versionado sem segredos
- `gemini_mcp_paths.py` - paths compartilhados da integracao

## Entry points operacionais

- `.agent/scripts/setup_gemini_mcp.py`
- `.agent/scripts/test_gemini_auth.py`

## Regra

Templates, paths e convencoes desta integracao devem viver aqui. Os scripts em `.agent/scripts/` continuam como comandos estaveis para o usuario e para o hub.
