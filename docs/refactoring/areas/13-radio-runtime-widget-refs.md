# 13 Radio Runtime Widget Refs

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Widget- und Window-Referenzen aus `_init_radio_runtime_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_runtime_state`

## Abhaengigkeiten und Seiteneffekte

- Es werden nur Attribute am App-Objekt gesetzt.
- Keine Tk-Widgets werden erzeugt.
- Pfad-, Runtime- und Theme-Initialisierung bleiben in `_init_radio_runtime_state`.
- Dict-Attribute werden weiterhin frisch initialisiert.

## Risiken

- Initialwerte muessen exakt erhalten bleiben.
- Leere Dicts duerfen nicht zwischen App-Instanzen geteilt werden.
- Der neue Helper darf keine Pfad- oder Host-App-Logik uebernehmen.

## Performance Vorher

- Commit vorher: `9d7fb38d`
- Messbedingungen: reiner Widget-Referenz-Zuweisungsblock mit `SimpleNamespace`, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_runtime_widget_refs_inline`: best of 5 `0.6986332180003956 s`

## Durchgefuehrte Aenderungen

- `_init_radio_runtime_widget_refs` eingefuehrt.
- `_init_radio_runtime_state` delegiert den Widget-Referenzblock an den neuen Helper.
- Direkter Test fuer alle initialisierten Widget-Referenzen ergaenzt.

## Unveraendertes Sollverhalten

- Alle bisherigen Widget-, Button-, Window- und Drag-Origin-Attribute werden gesetzt.
- Datenbank-Source-Dicts starten weiterhin leer.
- Refresh- und Source-Check-Flags starten weiterhin mit `False`.
- Die restliche Runtime-Initialisierung bleibt unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-runtime-widget-refs.md`
- `docs/refactoring/performance/areas/13-radio-runtime-widget-refs.md`

## Hinzugefuegte Tests

- `test_init_radio_runtime_widget_refs_initializes_widget_state`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `256 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2492 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_runtime_widget_refs_helper`: best of 5 `0.736213780000071 s`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim App-Start und ist nicht laufzeitkritisch.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Der Test prueft Attribute auf einem `SimpleNamespace`, nicht auf einer echten Tk-App.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Bedienung aller Widget-Referenzen.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-runtime-widget-refs`.
