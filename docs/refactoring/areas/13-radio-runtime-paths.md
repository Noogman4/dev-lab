# 13 Radio Runtime Paths

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Radio-Pfadinitialisierung aus `_init_radio_runtime_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_runtime_state`

## Abhaengigkeiten und Seiteneffekte

- `build_radio_paths` bleibt die Quelle fuer Radio-Pfade.
- Log- und Logo-Cache-Pfad werden weiterhin aus `netmon_state_dir` abgeleitet.
- Widget-, Runtime- und Theme-Initialisierung bleiben ausserhalb des neuen Helpers.
- Keine Tk-Widgets werden erzeugt.

## Risiken

- Alle Pfadattribute muessen exakt erhalten bleiben.
- `radio_log_path` und `radio_logo_cache_dir` muessen weiterhin `netmon_state_dir` nutzen.
- Der Helper darf keine Runtime-Daten laden oder Theme-Logik ausfuehren.

## Performance Vorher

- Commit vorher: `8db1fc54`
- Messbedingungen: reiner Pfad-Zuweisungsblock mit `SimpleNamespace`, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_runtime_paths_inline`: best of 5 `1.462315311000566 s`

## Durchgefuehrte Aenderungen

- `_init_radio_runtime_paths` eingefuehrt.
- `_init_radio_runtime_state` delegiert die Pfadinitialisierung an den neuen Helper.
- Direkter Test fuer alle Pfadattribute ergaenzt.

## Unveraendertes Sollverhalten

- `netmon_config_dir` und `netmon_state_dir` kommen weiterhin aus `build_radio_paths`.
- Radio-DB-, Meta-, Stations-, Favorites- und Settings-Pfade bleiben unveraendert.
- `radio_log_path` zeigt weiterhin auf `logs/netmon_radio_app.log`.
- `radio_logo_cache_dir` zeigt weiterhin auf `radio_station_logos`.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-runtime-paths.md`
- `docs/refactoring/performance/areas/13-radio-runtime-paths.md`

## Hinzugefuegte Tests

- `test_init_radio_runtime_paths_initializes_radio_paths`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `257 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2493 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_runtime_paths_helper`: best of 5 `1.6442980319998242 s`

## Bewertung

- Der Helper fuegt nur kleinen Aufruf- und Test-Lambda-Overhead hinzu.
- Der Pfad laeuft einmal beim App-Start und ist nicht laufzeitkritisch.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Der Test prueft Pfadzuweisung mit Dummy-Pfaden, nicht echte Dateisystemmigration.
- Echte Pfaderzeugung ist weiterhin ueber bestehende `build_radio_paths`-Tests abgedeckt.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-runtime-paths`.
