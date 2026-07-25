# 13 Radio UI Recordings Source Mini Vars

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Recordings-, Source- und Mini-Player-StringVars aus `_init_radio_ui_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_ui_state`

## Abhaengigkeiten und Seiteneffekte

- Es werden nur uebersetzte `StringVar`-Initialwerte am App-Objekt gesetzt.
- Folder-Browser-Runtime-State bleibt weiterhin in `_init_radio_ui_folder_browser_runtime_state`.
- Logo-Runtime-State und Theme-Variable bleiben in diesem Schritt unveraendert.
- Der neue Helper erlaubt fuer Tests einen injizierten Var-Builder ohne Tk-Root.

## Risiken

- Recordings-Status muss weiterhin mit `Recording folder: 0 files` starten.
- Source-Status muss weiterhin mit `Source: Livestream | -` starten.
- Mini-Player-Quelle und Detail-Stream muessen weiterhin denselben Live-Default nutzen.
- Mini-Player-Status und Detail-Status muessen weiterhin denselben Ready-Default nutzen.
- Mini-Player-Detailwerte fuer Format, Genre, Bitrate, Zeit, Volume und EQ muessen ihre Defaults behalten.

## Performance Vorher

- Commit vorher: `c232ec31`
- Messbedingungen: Recordings-/Source-/Mini-Player-StringVars mit `SimpleNamespace`, Dummy-Var-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_ui_recordings_source_mini_vars_inline`: best of 5 `2.1157602540006337 s`

## Durchgefuehrte Aenderungen

- `_init_radio_ui_recordings_source_mini_vars` eingefuehrt.
- `_init_radio_ui_state` delegiert Recordings-, Source- und Mini-Player-Variablen an den neuen Helper.
- Direkter Test fuer uebersetzte Initialwerte, feste Detail-Defaults und Builder-Aufrufe ergaenzt.

## Unveraendertes Sollverhalten

- Recordings-Status startet weiterhin mit `Recording folder: 0 files`.
- Source-Status startet weiterhin mit `Source: Livestream | -`.
- Mini-Player startet weiterhin mit Live/Ready/Nothing-is-playing-Defaults.
- Mini-Player-Detailwerte starten weiterhin mit `-`, `--:--:--`, `50%` und `EQ Flat`.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-ui-recordings-source-mini-vars.md`
- `docs/refactoring/performance/areas/13-radio-ui-recordings-source-mini-vars.md`

## Hinzugefuegte Tests

- `test_init_radio_ui_recordings_source_mini_vars_initializes_values`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `281 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2517 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_ui_recordings_source_mini_vars_helper`: best of 5 `2.1356559060004656 s`

## Bewertung

- Der Helper liegt praktisch im gleichen Zeitbereich wie der Inline-Block.
- Der Pfad laeuft einmal beim UI-Start und ist nicht laufzeitkritisch.
- Der Hauptgewinn ist geringere Blockgroesse in `_init_radio_ui_state` und direkte Testbarkeit ohne Tk-Root.

## Bekannte Restrisiken

- Der direkte Test nutzt Dummy-Variablen statt echte Tk-Variablen.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Bedienung der Recordings-, Source- oder Mini-Player-Anzeigen.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-ui-recordings-source-mini-vars`.
