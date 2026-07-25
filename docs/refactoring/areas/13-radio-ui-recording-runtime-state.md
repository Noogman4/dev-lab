# 13 Radio UI Recording Runtime State

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Recording-Runtime-State aus `_init_radio_ui_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_ui_state`

## Abhaengigkeiten und Seiteneffekte

- Aufnahmeordner kommt weiterhin aus `app.radio_settings["recordings_dir"]`.
- Aufnahmeordner wird weiterhin als String getrimmt.
- Recording-Status-`StringVar`s bleiben in `_init_radio_ui_state`.
- Es werden keine Tk-Widgets erzeugt.

## Risiken

- Fehlender Aufnahmeordner muss weiterhin zu `""` werden.
- Button-Referenzen muessen weiterhin mit `None` starten.
- Blink-State muss weiterhin deaktiviert starten.

## Performance Vorher

- Commit vorher: `2f13a08d`
- Messbedingungen: reiner Recording-Runtime-State mit `SimpleNamespace`, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_ui_recording_runtime_state_inline`: best of 5 `0.5614635060001092 s`

## Durchgefuehrte Aenderungen

- `_radio_ui_recordings_dir` eingefuehrt.
- `_init_radio_ui_recording_runtime_state` eingefuehrt.
- `_init_radio_ui_state` delegiert den nicht-Tk Recording-Runtime-State an den neuen Helper.
- Direkte Tests fuer Aufnahmeordner-Normalisierung und Initialwerte ergaenzt.

## Unveraendertes Sollverhalten

- Recording-Prozess startet weiterhin mit `None`.
- Aufnahmeordner wird weiterhin aus den Settings uebernommen und getrimmt.
- Letzter Aufnahmepfad startet leer.
- Transport-, Panel- und Ordner-Buttons starten weiterhin mit `None`.
- Blink-State startet weiterhin aus.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-ui-recording-runtime-state.md`
- `docs/refactoring/performance/areas/13-radio-ui-recording-runtime-state.md`

## Hinzugefuegte Tests

- `test_radio_ui_recordings_dir_uses_stripped_setting_and_default`
- `test_init_radio_ui_recording_runtime_state_initializes_recording_state`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `269 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2505 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_ui_recording_runtime_state_helper`: best of 5 `0.5909943349997775 s`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim UI-Start und ist nicht laufzeitkritisch.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen den Runtime-State ohne echte Tk-App.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Aufnahme-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-ui-recording-runtime-state`.
