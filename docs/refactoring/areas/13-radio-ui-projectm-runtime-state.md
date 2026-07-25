# 13 Radio UI projectM Runtime State

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: projectM-Runtime-State aus `_init_radio_ui_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_ui_state`

## Abhaengigkeiten und Seiteneffekte

- Es werden nur projectM-Runtime-Attribute am App-Objekt gesetzt.
- projectM-Status-`StringVar`s bleiben in `_init_radio_ui_state`.
- Liste, Set und Dict werden weiterhin frisch pro App-Objekt erzeugt.
- Keine Tk-Widgets werden erzeugt.

## Risiken

- Mutable Defaults duerfen nicht zwischen App-Instanzen geteilt werden.
- Logpfad und Loghandle muessen leer starten.
- Der neue Helper darf keine projectM-Prozesse starten.

## Performance Vorher

- Commit vorher: `3a3ec5db`
- Messbedingungen: reiner projectM-Runtime-State mit `SimpleNamespace`, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_ui_projectm_runtime_state_inline`: best of 5 `0.2650483870002063 s`

## Durchgefuehrte Aenderungen

- `_init_radio_ui_projectm_runtime_state` eingefuehrt.
- `_init_radio_ui_state` delegiert den nicht-Tk projectM-Runtime-State an den neuen Helper.
- Direkter Test fuer Initialwerte und frische Mutable-Objekte ergaenzt.

## Unveraendertes Sollverhalten

- projectM-Prozess startet weiterhin mit `None`.
- projectM-Kommando, bekannte PIDs und Package-Probe starten leer.
- Loghandle und Logpfad starten unveraendert.
- projectM-Statusvariablen werden weiterhin danach im UI-Initialisierer erzeugt.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-ui-projectm-runtime-state.md`
- `docs/refactoring/performance/areas/13-radio-ui-projectm-runtime-state.md`

## Hinzugefuegte Tests

- `test_init_radio_ui_projectm_runtime_state_initializes_fresh_state`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `267 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2503 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_ui_projectm_runtime_state_helper`: best of 5 `0.2788309060006213 s`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim UI-Start und ist nicht laufzeitkritisch.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen den Runtime-State ohne echte Tk-App.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle projectM-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-ui-projectm-runtime-state`.
