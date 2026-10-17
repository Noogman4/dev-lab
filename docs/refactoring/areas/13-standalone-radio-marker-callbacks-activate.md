# 13 Standalone Radio Marker Callbacks Activate

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Binding und initiales Update der Standalone-Radio-Pane-Marker-Callbacks zusammen aktivieren
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Callback-Binding erfolgt weiterhin ueber `_standalone_radio_pane_bind_marker_callbacks`.
- Initiales Marker-Update erfolgt weiterhin ueber `_standalone_radio_pane_schedule_initial_marker_update`.
- Binding passiert weiterhin vor dem initialen Update.
- Alle erzeugten Marker-Callbacks bleiben unveraendert.

## Risiken

- Binding und initiales Update muessen in derselben Reihenfolge laufen.
- Initiales Update muss denselben Update-Callback erhalten.
- Binding-Fehler duerfen nicht versehentlich geschluckt werden.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `32cc5210`
- Messbedingungen: Dummy-Container, Dummy-Binding-Plan, Dummy-Callbacks, Dummy-Binder und Dummy-Scheduler, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_callbacks_activate_inline`: best of 5 `138 ns`

## Geplante kleine Aenderung

- Binding plus initiales Update in `_standalone_radio_pane_activate_marker_callbacks` extrahieren.
- Direkte Tests fuer Reihenfolge und Fehlerpropagation ergaenzen.
- Restlichen Marker-Installer unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_activate_marker_callbacks` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer Binding und initiales Update.
- Tests fuer Bindung-vor-Scheduling und Binding-Fehler ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Container, Pane und Grip werden weiterhin mit denselben Callbacks gebunden.
- Initiales Marker-Update wird weiterhin nach dem Binding geplant.
- Marker-Install gibt weiterhin den Marker zurueck.
- Fehlerverhalten der Binder bleibt unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-callbacks-activate.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-callbacks-activate.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_activate_marker_callbacks_binds_then_schedules`
- `test_standalone_radio_pane_activate_marker_callbacks_propagates_binding_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `158 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `160 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2396 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_callbacks_activate_helper`: best of 5 `189 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-callbacks-activate`.
