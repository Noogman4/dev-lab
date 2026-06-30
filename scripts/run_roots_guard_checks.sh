#!/usr/bin/env bash
set -u

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

if [ -x "$PROJECT_ROOT/.venv/bin/python" ]; then
  PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi

printf "== Roots Guard Checks ==\n"
printf "Projekt: %s\n" "$PROJECT_ROOT"
printf "Python: %s\n" "$PYTHON_BIN"

if [ -n "${DISPLAY:-}" ]; then
  printf "DISPLAY: %s\n" "$DISPLAY"
  printf "UI-Smoke: aktiv, falls Tk-Smoke lokal moeglich ist\n"
else
  printf "DISPLAY: nicht gesetzt\n"
  printf "UI-Smoke: nur Quelltests, Tk-Smoke wird uebersprungen\n"
fi

printf "\n== UI ==\n"
"$PYTHON_BIN" -m pytest -q tests/test_netmon_roots_guard_ui.py || exit $?

printf "\n== Controller ==\n"
"$PYTHON_BIN" -m pytest -q tests/test_roots_baseline_guard_controller.py
