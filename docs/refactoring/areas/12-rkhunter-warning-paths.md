# 12 rkhunter Warning Paths

## Ausgangszustand

- Datei: `netmon/services/rkhunter_analysis_service.py`
- Fokus dieses Schritts: Pfadextraktion aus rkhunter-Warnzeilen
- Bestehende Tests: `tests/test_rkhunter_analysis_service.py`
- Indirekte Aufrufer: rkhunter-Analyse, Script-False-Positive-Erkennung, Propupd-Gate

## Abhaengigkeiten und Seiteneffekte

- Dieser Schritt nutzt nur bereits gelieferte rkhunter-Ausgabe.
- Keine rkhunter-Kommandos geaendert.
- Keine sudo- oder Root-Pfade geaendert.
- Keine `dpkg`- oder `file`-Verifikationskommandos geaendert.
- Keine Propupd-, Repair- oder Restore-Pfade geaendert.

## Risiken

- Pfade aus `replaced by script`-Warnungen muessen weiterhin erkannt werden.
- Pfade aus `[ Warning ]`-Zeilen muessen weiterhin nur fuer System-Binary-Prefixe erkannt werden.
- Doppelte Pfade muessen weiterhin in erster Reihenfolge dedupliziert werden.
- ANSI-Sequenzen muessen weiterhin vor der Pfadextraktion entfernt werden.

## Performance Vorher

- Commit vorher: `fc3742ee`
- Messbedingungen: direkter Aufruf von `extract_replaced_script_paths` und `extract_warning_command_paths` mit synthetischer rkhunter-Ausgabe, `time.perf_counter()`, 100 Wiederholungen.
- `rkhunter_warning_path_extractors`: Median `0.0650 ms`

## Geplante kleine Aenderung

- Direkte Tests fuer gemeinsame Pfadextraktion ergaenzen.
- Gemeinsame Deduplizierung und optionale Pfadfilterung in einen internen Helper extrahieren.
- Klassifizierung, Risk-Logik und Propupd-Gate unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_extract_unique_paths_from_lines` eingefuehrt.
- `extract_replaced_script_paths` nutzt den Helper fuer `replaced by script`-Zeilen.
- `extract_warning_command_paths` nutzt den Helper fuer `[ Warning ]`-Zeilen und behaelt den System-Binary-Prefixfilter bei.
- Keine rkhunter-Kommandos, Root-Pfade oder Analyseentscheidungen geaendert.

## Unveraendertes Sollverhalten

- Pfadlisten bleiben dedupliziert und in Eingabereihenfolge.
- `extract_replaced_script_paths` liefert weiterhin alle Pfade aus passenden Script-Warnungen.
- `extract_warning_command_paths` liefert weiterhin nur System-Binary-Pfade.
- Packaged-Script-False-Positive-Erkennung bleibt unveraendert.

## Betroffene Dateien

- `netmon/services/rkhunter_analysis_service.py`
- `tests/test_rkhunter_analysis_service.py`
- `docs/refactoring/areas/12-rkhunter-warning-paths.md`
- `docs/refactoring/performance/areas/12-rkhunter-warning-paths.md`

## Hinzugefuegte Tests

- `test_extract_unique_paths_from_lines_deduplicates_matching_lines`
- `test_extract_unique_paths_from_lines_applies_path_filter`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_rkhunter_analysis_service.py`: `14 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_rkhunter_analysis_service.py`: `16 passed`
- `.venv/bin/python -m ruff check netmon/services/rkhunter_analysis_service.py tests/test_rkhunter_analysis_service.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/services/rkhunter_analysis_service.py tests/test_rkhunter_analysis_service.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/services/rkhunter_analysis_service.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_rkhunter_analysis_service.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2198 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `rkhunter_warning_path_extractors`: Median `0.0778 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Differenz von `0.0128 ms` liegt fuer diesen kleinen Parserpfad im Messrauschen.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Parser-Tests nutzen synthetische rkhunter-Ausgaben.
- Der GUI-Smoke prueft Startbarkeit, aber keinen echten rkhunter-Scan.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `12-rkhunter-warning-paths`.
