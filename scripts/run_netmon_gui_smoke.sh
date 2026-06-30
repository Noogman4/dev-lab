#!/usr/bin/env bash
set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

if [ -x "$PROJECT_ROOT/.venv/bin/python" ]; then
  PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi

if ! command -v xvfb-run >/dev/null 2>&1; then
  printf "Fehler: xvfb-run wurde nicht gefunden.\n" >&2
  exit 2
fi

printf "== NetMon GUI Smoke ==\n"
printf "Projekt: %s\n" "$PROJECT_ROOT"
printf "Python: %s\n" "$PYTHON_BIN"
printf "Runner: %s\n" "$(command -v xvfb-run)"

exec xvfb-run -a "$PYTHON_BIN" -m netmon.main --headless-smoke "$@"
