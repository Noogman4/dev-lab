# 05 Core Tooling

## Ausgangszustand

- Datei: `netmon/core/tooling.py`
- Funktionen: `has_cmd`, `get_cmd_path`, `get_user_pictures_dir`, `load_speedtest_module_from_file`, `check_speedtest_module_available`
- Direkte Tests vor Beginn: keine dedizierte `core/tooling`-Testdatei
- Indirekte Aufrufer: App-Preflight, Speedtest, Backup-/Bilderordner-Helfer, diverse Feature-Controller ueber App-Aliase

## Abhaengigkeiten und Seiteneffekte

- `has_cmd` und `get_cmd_path` nutzen `shutil.which`.
- `get_user_pictures_dir` kann `xdg-user-dir PICTURES` ausfuehren, faellt dann auf `~/Bilder`, `~/Pictures`, `~` zurueck.
- Speedtest-Lader importiert eine Python-Datei per `importlib.util`.
- Keine Root-Rechte.
- Keine sicherheitskritischen Systembefehle.
- Keine GUI-Verbindung.
- Keine Threads oder Timer.

## Risiken

- Speedtest-Kandidatensuche darf Reihenfolge und Fehlermeldung nicht aendern.
- `get_user_pictures_dir` darf keine nicht existierenden `xdg-user-dir`-Pfade zurueckgeben.
- Fehlende Speedtest-Funktionen muessen weiterhin gemeldet werden.

## Performance Vorher

- Commit vorher: `7324176d`
- Messbedingungen: temporaeres Speedtest-Modul, `time.perf_counter()`, 20 Wiederholungen.
- `has_cmd_python`: Median `0.023 ms`
- `get_cmd_path_python`: Median `0.023 ms`
- `check_speedtest_module_available`: Median `0.050 ms`

## Geplante kleine Aenderung

- Bilderordner-Fallbacks in einen internen Helfer extrahieren.
- Speedtest-Kandidatenaufbau und eindeutige Kandidatenliste in interne Helfer extrahieren.
- Verhalten unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_existing_dir` fuer existierende Ordnerpfade eingefuehrt.
- `_picture_fallback_dirs` fuer `~/Bilder` und `~/Pictures` eingefuehrt.
- `_speedtest_module_candidates` fuer die Kandidatenreihenfolge eingefuehrt.
- `_unique_absolute_paths` fuer eindeutige absolute Speedtest-Kandidaten eingefuehrt.
- Oeffentliche Funktionssignaturen und Rueckgabewerte unveraendert gelassen.

## Unveraendertes Sollverhalten

- `has_cmd` und `get_cmd_path` nutzen weiterhin `shutil.which`.
- `get_user_pictures_dir` bevorzugt weiterhin einen gueltigen `xdg-user-dir PICTURES`-Pfad.
- Fallback-Reihenfolge bleibt `~/Bilder`, `~/Pictures`, `~`.
- Speedtest-Modulkandidaten bleiben in gleicher Reihenfolge.
- Fehlende Speedtest-Funktionen werden weiterhin als Liste gemeldet.

## Betroffene Dateien

- `netmon/core/tooling.py`
- `tests/test_core_tooling.py`
- `docs/refactoring/areas/05-core-tooling.md`
- `docs/refactoring/performance/areas/05-core-tooling.md`

## Hinzugefuegte Tests

- `tests/test_core_tooling.py`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_core_tooling.py`: `6 passed` vor Refactoring
- `.venv/bin/python -m compileall -q netmon/core/tooling.py tests/test_core_tooling.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check netmon/core/tooling.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check tests/test_core_tooling.py`: bestanden
- `.venv/bin/python -m ruff check netmon/core/tooling.py tests/test_core_tooling.py`: bestanden
- `.venv/bin/python -m pytest tests/test_core_tooling.py tests/test_speedtest_module.py`: `79 passed`

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest tests/test_core_tooling.py tests/test_speedtest_module.py tests/test_netmon_dependency_installer.py tests/test_netmon_settings_tab.py`: `127 passed`
- `make roots-guard-smoke`: `7 passed, 1 skipped`
- `make roots-guard-checks`: UI `7 passed, 1 skipped`, Controller `90 passed`
- `.venv/bin/python -m pytest`: `2169 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: bestanden ausserhalb der Sandbox wegen `xvfb-run`/Tk-Displayzugriff

## Performance Nachher

- `has_cmd_python`: Median `0.024 ms`
- `get_cmd_path_python`: Median `0.023 ms`
- `check_speedtest_module_available`: Median `0.054 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests fuer `xdg-user-dir` nutzen Mocks und fuehren kein echtes Desktop-Tool aus.
- Speedtest-Modulimport wird mit temporaeren Modulen getestet, nicht mit allen Installationspfaden.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `05-core-tooling`.
