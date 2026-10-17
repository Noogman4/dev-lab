# 13 Standalone Radio Marker Bind Events

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Binding-Installation fuer ein Standalone-Radio-Pane-Marker-Widget aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Widget-Events werden weiterhin mit `add="+"` gebunden.
- Binding-Fehler werden weiterhin pro Widget ignoriert.
- Nach einem Binding-Fehler werden die restlichen Bindings dieses Widgets weiterhin nicht versucht.
- Callback-Erzeugung, Drag-Logik und Initial-Update bleiben unveraendert.

## Risiken

- `add="+"` muss erhalten bleiben, damit bestehende Tk-Bindings nicht ersetzt werden.
- Die Try/Except-Grenze muss weiterhin die komplette Binding-Liste eines Widgets umfassen.
- Die Reihenfolge der Bindings muss unveraendert bleiben.
- Der Installer muss die Legacy-Source-Hinweise weiterhin enthalten.

## Performance Vorher

- Commit vorher: `abdd6475`
- Messbedingungen: direkter Batch-Bind-Pfad mit Dummy-Widget und drei Dummy-Bindings, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_bind_events_inline`: best of 5 `265 ns`

## Geplante kleine Aenderung

- Batch-Binding in `_standalone_radio_pane_bind_marker_events` extrahieren.
- Direkte Tests fuer erfolgreiche Bindings und Stop-nach-Fehler-Pfad ergaenzen.
- Die beiden lokalen Binding-Schleifen im Installer auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_bind_marker_events` eingefuehrt.
- Installer nutzt den Helper fuer Container/Pane-Update-Bindings und Grip-Drag-Bindings.
- Tests fuer `add="+"` und ignorierte Binding-Fehler ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Container und Pane erhalten weiterhin Configure, ButtonRelease-1 und B1-Motion fuer Marker-Updates.
- Grip erhaelt weiterhin Button-1, B1-Motion und ButtonRelease-1 fuer Drag-Callbacks.
- Binding-Fehler werden weiterhin ignoriert.
- Der Tk-Eventfluss der Drag-Callbacks bleibt unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-bind-events.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-bind-events.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_bind_marker_events_binds_all_with_add`
- `test_standalone_radio_pane_bind_marker_events_stops_and_ignores_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `147 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `149 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2385 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_bind_events_helper`: best of 5 `290 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen Dummy-Widgets, nicht echte Tk-Bindings.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-bind-events`.
