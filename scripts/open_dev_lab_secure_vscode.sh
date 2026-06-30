#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE_FILE="$PROJECT_ROOT/dev-lab-secure.code-workspace"
DISABLED_LIST="$PROJECT_ROOT/.vscode/secure-disabled-extensions.txt"
PROFILE_NAME="dev-lab-secure"

if ! command -v code >/dev/null 2>&1; then
  printf "Fehler: 'code' wurde nicht gefunden.\n" >&2
  exit 1
fi

if [[ ! -f "$WORKSPACE_FILE" ]]; then
  printf "Fehler: Workspace-Datei fehlt: %s\n" "$WORKSPACE_FILE" >&2
  exit 1
fi

ARGS=(--new-window --profile "$PROFILE_NAME")

while IFS= read -r ext; do
  [[ -n "${ext}" ]] || continue
  ARGS+=(--disable-extension "$ext")
done < "$DISABLED_LIST"

ARGS+=("$WORKSPACE_FILE")

exec code "${ARGS[@]}"
