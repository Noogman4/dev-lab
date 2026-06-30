# Dev Lab

## Roots Baseline Guard Checks

Fuer den `Roots Baseline Guard` gibt es jetzt zwei schnelle Projektchecks:

- `make roots-guard-smoke`
  - startet den UI-Smoke-Test fuer den `Roots Baseline Guard`
  - enthaelt Quelltests und optional einen kleinen Tk-Smoke-Test, wenn lokal ein `DISPLAY` verfuegbar ist
- `make roots-guard-checks`
  - startet den UI-Smoke-Test plus die kompletten `Roots Baseline Guard`-Controller-Tests

Direkt ueber Skript geht es ebenfalls:

- `bash scripts/run_roots_guard_smoke.sh`
- `bash scripts/run_roots_guard_checks.sh`

