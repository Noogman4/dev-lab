#!/usr/bin/env bash
set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

if [ -x "$PROJECT_ROOT/.venv/bin/python" ]; then
  PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi

printf "== Roots Guard Smoke ==\n"
printf "Projekt: %s\n" "$PROJECT_ROOT"
printf "Python: %s\n" "$PYTHON_BIN"

if [ -n "${DISPLAY:-}" ]; then
  printf "DISPLAY: %s\n" "$DISPLAY"
  printf "Modus: Quelltests + optionaler Tk-Smoke-Test\n"
else
  printf "DISPLAY: nicht gesetzt\n"
  printf "Modus: Quelltests; Tk-Smoke-Test wird uebersprungen\n"
fi

printf "\n== Testlauf ==\n"
"$PYTHON_BIN" -m pytest -q tests/test_netmon_roots_guard_ui.py
