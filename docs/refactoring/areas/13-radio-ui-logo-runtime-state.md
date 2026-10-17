# 13 Radio UI Logo Runtime State

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Logo-, Mini-Player- und projectM-Zeitstempel-State aus `_init_radio_ui_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_ui_state`

## Abhaengigkeiten und Seiteneffekte

- Mini-Player-`StringVar`s bleiben in `_init_radio_ui_state`.
- Logo- und Mini-Player-Fotoreferenzen starten weiterhin mit `None`.
- Logo-Cache-Keys starten weiterhin leer.
- Trace-Liste wird weiterhin frisch erzeugt.

## Risiken

- Trace-Liste darf nicht zwischen App-Instanzen geteilt werden.
- projectM-Zeitstempel muessen weiterhin leer starten.
- Der neue Helper darf keine Tk-Widgets oder Bilder erzeugen.

## Performance Vorher

- Commit vorher: `f0b234d9`
- Messbedingungen: reiner Logo-/Mini-Runtime-State mit `SimpleNamespace`, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_ui_logo_runtime_state_inline`: best of 5 `0.3539282910005568 s`

## Durchgefuehrte Aenderungen

- `_init_radio_ui_logo_runtime_state` eingefuehrt.
- `_init_radio_ui_state` delegiert den nicht-Tk Logo-/Mini-Runtime-State an den neuen Helper.
- Direkter Test fuer Initialwerte und frische Trace-Liste ergaenzt.

## Unveraendertes Sollverhalten

- projectM-Zeitstempel starten weiterhin leer.
- Logo-Labels und Mini-Player-Buttons starten weiterhin mit `None`.
- Foto-Referenzen und Logo-Keys starten unveraendert.
- Aktives Kontextmenue startet weiterhin mit `None`.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-ui-logo-runtime-state.md`
- `docs/refactoring/performance/areas/13-radio-ui-logo-runtime-state.md`

## Hinzugefuegte Tests

- `test_init_radio_ui_logo_runtime_state_initializes_fresh_state`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `273 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2509 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_ui_logo_runtime_state_helper`: best of 5 `0.4214983910005685 s`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim UI-Start und ist nicht laufzeitkritisch.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen den Runtime-State ohne echte Tk-App.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Mini-Player- oder Logo-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-ui-logo-runtime-state`.
