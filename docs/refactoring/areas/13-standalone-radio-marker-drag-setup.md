# 13 Standalone Radio Marker Drag Setup

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Drag-State- und Sash-Callback-Bau aus dem Basis-Callback-Helper herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_marker_base_callbacks`

## Abhaengigkeiten und Seiteneffekte

- Drag-State-Bau bleibt bei `_standalone_radio_pane_drag_state`.
- Sash-Callback-Bau bleibt bei `_standalone_radio_pane_sash_callback`.
- Place-, Update- und Schedule-Callback-Bau bleiben im Basis-Callback-Helper.
- Marker-Callback-Orchestrator und Binding-Aktivierung bleiben unveraendert.

## Risiken

- Drag-State muss weiterhin vor dem Sash-Callback gebaut werden.
- Sash-Callback muss weiterhin das Pane erhalten.
- Der Basis-Callback-Helper muss Drag-State und Sash-Setter unveraendert weiterreichen.
- Fehler aus dem Drag-Setup duerfen nicht versehentlich geschluckt werden.

## Performance Vorher

- Commit vorher: `1075de52`
- Messbedingungen: Dummy-Container, Dummy-Pane, Dummy-Marker, Dummy-Callbacks, Dummy-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_base_callbacks_current`: best of 5 `446 ns`

## Geplante kleine Aenderung

- Drag-State- und Sash-Callback-Bau in `_standalone_radio_pane_marker_drag_setup` extrahieren.
- Direkte Tests fuer Builder-Reihenfolge, Rueckgabewert und Fehlerpropagation ergaenzen.
- Basis-Callback-Test auf Drag-Setup-Delegation umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_drag_setup` eingefuehrt.
- `_standalone_radio_pane_marker_base_callbacks` nutzt den neuen Drag-Setup-Helper.
- Tests fuer Drag-Setup, Fehlerpropagation und Basis-Callback-Delegation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Drag-State und Sash-Setter bleiben erste Werte des Basis-Callback-Tuples.
- Place-, Update- und Schedule-Callback-Reihenfolge bleibt unveraendert.
- Der Marker-Callback-Orchestrator gibt weiterhin dasselbe finale Callback-Tuple zurueck.
- Marker-Parts-Installation erhaelt weiterhin dasselbe Callback-Tuple.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-drag-setup.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-drag-setup.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_drag_setup_builds_state_and_sash_callback`
- `test_standalone_radio_pane_marker_drag_setup_propagates_builder_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `200 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `202 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2438 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_base_callbacks_drag_setup_helper`: best of 5 `411 ns`

## Bewertung

- Das Drag-Setup ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Callbacks statt echter Tk-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-drag-setup`.
