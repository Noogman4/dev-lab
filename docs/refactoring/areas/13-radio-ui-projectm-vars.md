# 13 Radio UI projectM Vars

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: projectM-StringVars aus `_init_radio_ui_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_ui_state`

## Abhaengigkeiten und Seiteneffekte

- Es werden nur uebersetzte `StringVar`-Initialwerte am App-Objekt gesetzt.
- projectM-Runtime-State bleibt weiterhin in `_init_radio_ui_projectm_runtime_state`.
- Preset-Verzeichnis- und Sidecar-Logik bleiben unveraendert in den bestehenden Pfaden.
- Source-Anker fuer bestehende projectM-Hook-Tests bleiben am Delegationspunkt in `_init_radio_ui_state` erhalten.
- Der neue Helper erlaubt fuer Tests einen injizierten Var-Builder ohne Tk-Root.

## Risiken

- projectM-Status muss weiterhin mit `projectM not installed` starten.
- Meta- und History-Texte muessen ihre Defaults behalten.
- Installations- und Preset-Status muessen weiterhin uebersetzt initialisiert werden.
- Attach-Status muss weiterhin leer starten.
- Bestehende Source-Anker-Tests duerfen durch die Auslagerung nicht gebrochen werden.

## Performance Vorher

- Commit vorher: `2f5d4014`
- Messbedingungen: projectM-StringVars mit `SimpleNamespace`, Dummy-Var-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_ui_projectm_vars_inline`: best of 5 `1.1708939939999254 s`

## Durchgefuehrte Aenderungen

- `_init_radio_ui_projectm_vars` eingefuehrt.
- `_init_radio_ui_state` delegiert projectM-Status-, Meta-, History-, Install-, Preset- und Attach-Variablen an den neuen Helper.
- Source-Anker fuer projectM-Preset-Texte in `_init_radio_ui_state` erhalten.
- Direkter Test fuer uebersetzte Initialwerte und Builder-Aufrufe ergaenzt.

## Unveraendertes Sollverhalten

- projectM-Status startet weiterhin mit `projectM not installed`.
- projectM-Meta startet weiterhin mit `PID: - | Log: -`.
- projectM-History startet weiterhin mit `Last started: - | Last stopped: -`.
- projectM-Installationsstatus startet weiterhin mit dem Checking-Text.
- projectM-Presetstatus und Preset-Hinweis starten weiterhin mit ihren bisherigen Defaults.
- Attach-Status startet weiterhin leer.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-ui-projectm-vars.md`
- `docs/refactoring/performance/areas/13-radio-ui-projectm-vars.md`

## Hinzugefuegte Tests

- `test_init_radio_ui_projectm_vars_initializes_translated_values`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `278 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2514 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_ui_projectm_vars_helper`: best of 5 `1.2696884100005263 s`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim UI-Start und ist nicht laufzeitkritisch.
- Der Hauptgewinn ist geringere Blockgroesse in `_init_radio_ui_state` und direkte Testbarkeit ohne Tk-Root.

## Bekannte Restrisiken

- Der direkte Test nutzt Dummy-Variablen statt echte Tk-Variablen.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Bedienung der projectM-Controls.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-ui-projectm-vars`.
