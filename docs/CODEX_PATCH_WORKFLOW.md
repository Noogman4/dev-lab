# CODEX Patch Workflow (wenn `apply_patch` scheitert)

## Problem
In manchen Agent-Umgebungen kann `apply_patch` mit einer `bwrap`/Namespace-Fehlermeldung scheitern.
Das ist ein Umgebungsproblem, nicht zwingend ein Fehler im Projektcode.

Typische Symptome:
- `bwrap: No permissions to create a new namespace`
- `apply_patch` bricht sofort ab

## Empfohlener Ablauf
1. `bash scripts/dev_setup_check.sh` ausführen.
2. Auf Abschnitt `Codex-Workflow` achten.
3. Wenn `apply_patch` blockiert ist:
   - minimale, klar abgegrenzte Dateiänderungen durchführen
   - danach immer verifizieren:
     - `python -m py_compile <betroffene_dateien>`
     - `ruff check <betroffene_dateien>`
     - `pytest -q <relevante_tests>`
4. Änderungen klein halten und jeden Schritt mit Tests bestätigen.

## Ziel
Auch ohne `apply_patch` soll der Workflow reproduzierbar, sicher und testgetrieben bleiben.
