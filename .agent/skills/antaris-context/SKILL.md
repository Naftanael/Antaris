---
name: antaris-context
description: Bootstrap Antaris vault context, memory, brain search and session management. Use at the start of any session or when the user references vault knowledge, PKM, projects, or Obsidian notes.
---

# Antaris Context Layer

Antaris is the identity, memory, and context system built on top of the Hermes runtime.
This skill provides access to the vault, brain, and operational memory.

## Bootstrap (start of every session)

```bash
python3 /home/antaris/Documentos/Antaris/.agent/scripts/antigravity_hub.py bootstrap
```

Loads: context manifest, persistent memory (4 files), recent vault activity. ~3-5k tokens.

## Brain Search (semantic + lexical retrieval)

```bash
python3 /home/antaris/Documentos/Antaris/.agent/scripts/antigravity_hub.py brain-query "your question" --mode hybrid --limit 5
```

Modes: `lexical`, `semantic`, `hybrid`. Uses 11k+ embedded chunks from brain.db.

## Vault Search (metadata index)

```bash
python3 /home/antaris/Documentos/Antaris/.agent/scripts/antigravity_hub.py search "query" --limit 5
```

## Related Notes

```bash
python3 /home/antaris/Documentos/Antaris/.agent/scripts/antigravity_hub.py related "Note Title"
```

## Recent Notes

```bash
python3 /home/antaris/Documentos/Antaris/.agent/scripts/antigravity_hub.py recent --days 7 --limit 10
```

## Session Checkpoint (end of session)

```bash
python3 /home/antaris/Documentos/Antaris/.agent/scripts/antigravity_hub.py checkpoint --summary "what was done"
```

## Health Check

```bash
python3 /home/antaris/Documentos/Antaris/.agent/scripts/antigravity_hub.py doctor
```

## Architecture

- **Vault**: /home/antaris/Documentos/Antaris (Obsidian, PARA structure)
- **Brain**: .agent/brain.db (SQLite FTS5 + embeddings, 11k+ chunks)
- **Memory**: .agent/memory/ (project-state, session-log, user-preferences, lessons-learned)
- **Personas PKM**: Arquiteto, Executor, Engenheiro, Sintetizador
- **Hermes config**: ~/.hermes/ (skin=antaris, SOUL.md)

## Key Conventions

- Always bootstrap at session start
- Always checkpoint at session end
- Use brain-query before reading full notes (saves tokens)
- Respond in pt-BR unless asked otherwise
- Be direto, terminal-first, sem fluff
