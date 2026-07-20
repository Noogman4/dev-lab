# 07 Process Guard

## Ausgangszustand

- Dateien: `netmon/services/process_guard_service.py`, `netmon/features/process_guard_controller.py`
- Fokus dieses Schritts: `ProcessGuardService.evaluate_process`
- Bestehende Tests: `tests/test_process_guard_service.py`, `tests/test_process_guard_controller.py`, `tests/test_netmon_process_guard_ui.py`
- Indirekte Aufrufer: Process-Guard-Check, Monitoring, Trustlist, UI-Tab

## Abhaengigkeiten und Seiteneffekte

- Dieser Schritt nutzt nur bereits uebergebene Prozessdaten.
- Keine Prozesse werden beendet.
- Keine Root-Rechte.
- Kein Subprocess-Aufruf im refaktorierten Pfad.
- Keine Aenderung an `snapshot_processes`, `run_check` oder Trustlist-Schreibpfaden.

## Risiken

- Risk-Level-Schwellen duerfen sich nicht aendern.
- Anzeige fuer fehlende Executable-/CWD-/Cmdline-Daten muss stabil bleiben.
- Reason-Texte, Score-Aufbau und Sortierung duerfen sich nicht aendern.
- Trusted-Findings muessen weiterhin unveraendert herausgefiltert werden.

## Performance Vorher

- Commit vorher: `f9df361a`
- Messbedingungen: direkter Aufruf von `ProcessGuardService.evaluate_process`, synthetischer Temp-Shell-Prozess mit Browser-Parent, `time.perf_counter()`, 100 Wiederholungen.
- `process_guard_evaluate_process`: Median `0.015 ms`

## Geplante kleine Aenderung

- Verhaltenstests fuer mittlere Risk-Level-Schwelle und Kernel-Thread-Anzeige ergaenzen.
- Risk-Level-Ableitung und Executable-Anzeigewert in interne Helfer extrahieren.
- Score-Berechnung, Finding-Struktur und oeffentliche Methoden unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_risk_level_for_score` fuer die Risk-Level-Schwellen eingefuehrt.
- `_display_exe` fuer den angezeigten Executable-Wert eingefuehrt.
- `evaluate_process` nutzt diese Helfer nach unveraenderter Score-Berechnung.
- Oeffentliche Methodensignaturen und Rueckgabestruktur unveraendert gelassen.

## Unveraendertes Sollverhalten

- Score-Schwellen bleiben: ab `6` high, ab `3` medium, sonst low.
- Fehlende Executable bei leeren CWD-/Cmdline-Daten wird weiterhin als `Kernel-Thread` angezeigt.
- Reason-Texte, Score-Aufbau und Summary bleiben unveraendert.
- `run_check` und `detect_new_findings` filtern Trustlist-Eintraege weiterhin ueber `is_trusted`.
- Keine Prozesse werden beendet oder veraendert.

## Betroffene Dateien

- `netmon/services/process_guard_service.py`
- `tests/test_process_guard_service.py`
- `docs/refactoring/areas/07-process-guard.md`
- `docs/refactoring/performance/areas/07-process-guard.md`

## Hinzugefuegte Tests

- `test_evaluate_process_maps_downloads_only_to_medium_risk`
- `test_evaluate_process_uses_kernel_thread_display_for_empty_paths`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_process_guard_service.py`: `15 passed` vor Refactoring
- `.venv/bin/python -m compileall -q netmon/services/process_guard_service.py tests/test_process_guard_service.py`: bestanden
- `.venv/bin/python -m ruff check netmon/services/process_guard_service.py tests/test_process_guard_service.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check netmon/services/process_guard_service.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check tests/test_process_guard_service.py`: bestanden
- `.venv/bin/python -m pytest tests/test_process_guard_service.py`: `15 passed`
- `.venv/bin/python -m pytest tests/test_process_guard_service.py tests/test_process_guard_controller.py tests/test_netmon_process_guard_ui.py`: `84 passed`

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2173 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: bestanden ausserhalb der Sandbox wegen `xvfb-run`/Tk-Displayzugriff

## Performance Nachher

- `process_guard_evaluate_process`: Median `0.018 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Die Service-Tests nutzen synthetische Prozessdaten, nicht echte laufende Prozesse.
- Der GUI-Smoke prueft Startbarkeit, aber keine komplette Process-Guard-Interaktion.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `07-process-guard`.
