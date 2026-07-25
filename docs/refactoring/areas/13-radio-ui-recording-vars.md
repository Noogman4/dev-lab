# 13 Radio UI Recording Vars

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Recording-StringVars aus `_init_radio_ui_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_ui_state`

## Abhaengigkeiten und Seiteneffekte

- Es werden nur uebersetzte `StringVar`-Initialwerte am App-Objekt gesetzt.
- Recording-Runtime-State bleibt weiterhin in `_init_radio_ui_recording_runtime_state`.
- Playlist- und Folder-Browser-Initialisierung bleiben unveraendert.
- Der neue Helper erlaubt fuer Tests einen injizierten Var-Builder ohne Tk-Root.

## Risiken

- Recording-Status muss weiterhin mit `Recording off.` starten.
- Aufnahmeordner- und letzte-Datei-Text muessen ihre Defaults behalten.
- `_init_radio_ui_state` muss Runtime-State weiterhin vor den Recording-Variablen initialisieren.

## Performance Vorher

- Commit vorher: `36cf4b03`
- Messbedingungen: Recording-StringVars mit `SimpleNamespace`, Dummy-Var-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_ui_recording_vars_inline`: best of 5 `0.5318704139990587 s`

## Durchgefuehrte Aenderungen

- `_init_radio_ui_recording_vars` eingefuehrt.
- `_init_radio_ui_state` delegiert Recording-Status-, Ordner- und Datei-Variablen an den neuen Helper.
- Direkter Test fuer uebersetzte Initialwerte und Builder-Aufrufe ergaenzt.

## Unveraendertes Sollverhalten

- Recording-Status startet weiterhin mit `Recording off.`.
- Aufnahmeordner startet weiterhin mit `Aufnahmeordner: -`.
- Letzte Aufnahme startet weiterhin mit `Letzte Aufnahme: -`.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-ui-recording-vars.md`
- `docs/refactoring/performance/areas/13-radio-ui-recording-vars.md`

## Hinzugefuegte Tests

- `test_init_radio_ui_recording_vars_initializes_translated_values`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `279 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2515 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_ui_recording_vars_helper`: best of 5 `0.5746121180000046 s`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim UI-Start und ist nicht laufzeitkritisch.
- Der Hauptgewinn ist geringere Blockgroesse in `_init_radio_ui_state` und direkte Testbarkeit ohne Tk-Root.

## Bekannte Restrisiken

- Der direkte Test nutzt Dummy-Variablen statt echte Tk-Variablen.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Bedienung der Recording-Controls.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-ui-recording-vars`.
