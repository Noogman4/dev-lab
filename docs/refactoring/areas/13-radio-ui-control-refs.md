# 13 Radio UI Control Refs

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Control-Referenzen aus `_init_radio_ui_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_ui_state`

## Abhaengigkeiten und Seiteneffekte

- Es werden nur einfache UI-State-Attribute am App-Objekt gesetzt.
- `StringVar`s und echte Tk-Widgets bleiben in `_init_radio_ui_state`.
- Spalten- und Custom-Editor-State starten weiterhin leer.
- projectM-Button-Referenzen starten weiterhin mit `None`.

## Risiken

- `radio_light_state` muss weiterhin mit `gray` starten.
- `radio_station_column_vars` darf nicht zwischen App-Instanzen geteilt werden.
- Custom-Editor- und projectM-Button-Referenzen muessen weiterhin leer starten.

## Performance Vorher

- Commit vorher: `82f5de40`
- Messbedingungen: reiner Control-Ref-State mit `SimpleNamespace`, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_ui_control_refs_inline`: best of 5 `0.29353930199977185 s`

## Durchgefuehrte Aenderungen

- `_init_radio_ui_control_refs` eingefuehrt.
- `_init_radio_ui_state` delegiert Licht-, Kontext-, Spalten-, Custom-Editor- und projectM-Button-Referenzen an den neuen Helper.
- Direkter Test fuer Initialwerte und frisches Spalten-Dict ergaenzt.

## Unveraendertes Sollverhalten

- Radio-Lichtstatus startet weiterhin mit `gray`.
- Kontext-Sender-ID startet weiterhin leer.
- Custom-Editor und projectM-Button-Referenzen starten weiterhin mit `None`.
- Station-Column-State startet weiterhin als frisches Dict.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-ui-control-refs.md`
- `docs/refactoring/performance/areas/13-radio-ui-control-refs.md`

## Hinzugefuegte Tests

- `test_init_radio_ui_control_refs_initializes_fresh_state`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `274 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2510 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_ui_control_refs_helper`: best of 5 `0.3309513660005905 s`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim UI-Start und ist nicht laufzeitkritisch.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen den Runtime-State ohne echte Tk-App.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Editor- oder projectM-Button-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-ui-control-refs`.
