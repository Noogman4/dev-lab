# 06 Repository Guard

## Ausgangszustand

- Dateien: `netmon/services/repository_guard_service.py`, `netmon/features/repository_guard_controller.py`
- Fokus dieses Schritts: `RepositoryGuardService.build_findings`
- Bestehende Tests: `tests/test_repository_guard_service.py`, `tests/test_repository_guard_controller.py`
- Indirekte Aufrufer: Repository-Guard-Tab, Baseline-Vergleich, Export- und Detailfunktionen

## Abhaengigkeiten und Seiteneffekte

- Dieser Schritt nutzt nur bereits eingelesene Quellen, Fehler, Hilfsdateien und Keyring-Listen.
- Keine realen Repository- oder Paketquellen werden geaendert.
- Keine Root-Rechte.
- Kein Subprocess-Aufruf im refaktorierten Pfad.
- `file_exists_fn` bleibt injizierbar und wird nur fuer `signed-by`-Pruefungen genutzt.

## Risiken

- Finding-Codes, Schweregrade, IDs und Sortierung duerfen sich nicht aendern.
- Auxiliary-Dateien und globale Drittanbieter-Keyrings muessen weiterhin als Findings erscheinen.
- Runtime-/Parse-Fehler muessen weiterhin in Findings ueberfuehrt werden.
- Flatpak-Missing-Hinweis darf nur bei `flatpak_status == "missing"` entstehen.

## Performance Vorher

- Commit vorher: `d08b4676`
- Messbedingungen: direkter Aufruf von `RepositoryGuardService.build_findings`, synthetische Quellen/Fehler/Hilfsdateien/Keyrings, `time.perf_counter()`, 20 Wiederholungen.
- `repository_guard_build_findings`: Median `0.019 ms`

## Geplante kleine Aenderung

- Direkte Tests fuer Hilfsdatei- und Keyring-Findings ergaenzen.
- Finding-Erzeugung fuer Auxiliary-Dateien, globale Keyrings, Fehler und Flatpak-Missing in interne Helfer extrahieren.
- Verhalten, Sortierung und Rueckgabestruktur unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_auxiliary_file_findings` fuer Findings aus `.distUpgrade`, `.disabled` und Backup-Dateien eingefuehrt.
- `_global_keyring_findings` fuer globale Drittanbieter-Keyring-Hinweise eingefuehrt.
- `_repository_error_findings` fuer Runtime- und Parse-Fehler-Findings eingefuehrt.
- `_flatpak_missing_finding` fuer den Flatpak-nicht-installiert-Hinweis eingefuehrt.
- `build_findings` ruft diese Helfer auf und sortiert die komplette Finding-Liste weiterhin am Ende.

## Unveraendertes Sollverhalten

- Finding-Codes, Schweregrade, Titel, Summaries und Details bleiben unveraendert.
- Finales Sortierverhalten bleibt nach Severity-Rang und Finding-ID.
- `file_exists_fn` wird weiterhin nur fuer `signed-by`-Keyringpfade genutzt.
- Der Flatpak-Missing-Hinweis entsteht weiterhin nur bei `flatpak_status == "missing"`.
- Keine realen Repository-Dateien werden geschrieben oder veraendert.

## Betroffene Dateien

- `netmon/services/repository_guard_service.py`
- `tests/test_repository_guard_service.py`
- `docs/refactoring/areas/06-repository-guard.md`
- `docs/refactoring/performance/areas/06-repository-guard.md`

## Hinzugefuegte Tests

- `test_build_findings_adds_auxiliary_file_findings`
- `test_build_findings_adds_global_third_party_keyring_only`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_repository_guard_service.py`: `29 passed` vor Refactoring
- `.venv/bin/python -m compileall -q netmon/services/repository_guard_service.py tests/test_repository_guard_service.py`: bestanden
- `.venv/bin/python -m ruff check netmon/services/repository_guard_service.py tests/test_repository_guard_service.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check netmon/services/repository_guard_service.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check tests/test_repository_guard_service.py`: bestanden
- `.venv/bin/python -m pytest tests/test_repository_guard_service.py`: `29 passed`
- `.venv/bin/python -m pytest tests/test_repository_guard_service.py tests/test_repository_guard_controller.py`: `92 passed`

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2171 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: bestanden ausserhalb der Sandbox wegen `xvfb-run`/Tk-Displayzugriff

## Performance Nachher

- `repository_guard_build_findings`: Median `0.021 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Repository-Dateien werden in Tests ueber temporaere Dateien oder direkte Datenstrukturen abgebildet.
- Der GUI-Smoke prueft Startbarkeit, aber keine komplette Repository-Guard-Interaktion.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `06-repository-guard`.
