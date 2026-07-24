# 13 Standalone Radio Marker Bindings Activate

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Binding-Aktivierung fuer den Standalone-Radio-Pane-Marker aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Update-Bindings werden weiterhin ueber `_standalone_radio_pane_update_bindings` gebaut.
- Grip-Bindings werden weiterhin ueber `_standalone_radio_pane_grip_bindings` gebaut.
- Binding-Plan wird weiterhin ueber `_standalone_radio_pane_marker_binding_plan` gebaut.
- Aktivierung laeuft weiterhin ueber `_standalone_radio_pane_activate_marker_callbacks`.

## Risiken

- Update-, Start-, Drag- und End-Callbacks muessen unveraendert in die Binding-Builder fliessen.
- Binding-Plan muss Container, Pane und Grip weiterhin gleich verdrahten.
- Aktivierung muss weiterhin den Container, den Binding-Plan und den Update-Callback erhalten.
- Fehler duerfen im Composition-Helper nicht versehentlich geschluckt werden.

## Performance Vorher

- Commit vorher: `35f028a0`
- Messbedingungen: Dummy-Widgets, Dummy-Callbacks, Dummy-Binding-Builder, Dummy-Aktivierung, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_binding_activation_inline`: best of 5 `297 ns`

## Geplante kleine Aenderung

- Binding-Aktivierung in `_standalone_radio_pane_activate_marker_bindings` extrahieren.
- Direkte Tests fuer Builder-Reihenfolge, Aktivierungsargumente und Fehlerpropagation ergaenzen.
- Restlichen Marker-Installer unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_activate_marker_bindings` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer die Binding-Aktivierung.
- Tests fuer Builder-Reihenfolge, Aktivierungsargumente und Fehlerpropagation ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Container, Pane und Grip werden weiterhin mit denselben Callback-Sets gebunden.
- Initiales Marker-Update wird weiterhin ueber die bestehende Aktivierung geplant.
- Binding passiert weiterhin vor dem initialen Update.
- Marker-Install gibt weiterhin den Marker zurueck.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-bindings-activate.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-bindings-activate.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_activate_marker_bindings_builds_and_activates`
- `test_standalone_radio_pane_activate_marker_bindings_propagates_activation_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `174 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `176 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2412 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_binding_activation_helper`: best of 5 `321 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-bindings-activate`.
