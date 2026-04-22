#!/usr/bin/env bash
set -euo pipefail

ANTARIS_VAULT_ROOT="${ANTARIS_VAULT_ROOT:-__ANTARIS_VAULT_ROOT__}"

if [[ ! -f "$ANTARIS_VAULT_ROOT/.agent/scripts/antigravity_hub.py" ]]; then
  echo "Antaris launcher error: antigravity_hub.py not found in $ANTARIS_VAULT_ROOT" >&2
  exit 1
fi

exec python3 "$ANTARIS_VAULT_ROOT/.agent/scripts/antigravity_hub.py" launch-hermes "$@"
