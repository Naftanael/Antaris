# Obsidian Integration

Diretorio canonico da integracao entre o vault Antaris e os scripts `obsidian_*`.

## O que fica aqui

- `obsidian_paths.py` - resolucao compartilhada de paths do vault

## O que continua em .agent/scripts

- `obsidian_bootstrap.py`
- `obsidian_checkpoint.py`
- `obsidian_index.py`
- `obsidian_recent.py`
- `obsidian_related.py`
- `obsidian_search.py`
- `obsidian_summary.py`

Esses scripts continuam como entrypoints publicos para manter a interface do vault estavel.

## Regra

Qualquer path compartilhado, convencao do vault ou utilitario comum da integracao Obsidian deve nascer aqui e ser consumido pelos scripts, em vez de ser duplicado em cada arquivo.
