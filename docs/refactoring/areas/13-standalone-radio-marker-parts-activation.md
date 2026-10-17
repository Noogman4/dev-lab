# 13 Standalone Radio Marker Parts Activation

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Callback-Tuple-Entpackung und Binding-Aktivierung aus der Marker-Parts-Installation herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_install_marker_parts`

## Abhaengigkeiten und Seiteneffekte

- Callback-Bau bleibt bei `_standalone_radio_pane_marker_callbacks`.
- Binding-Aktivierung bleibt bei `_standalone_radio_pane_activate_marker_bindings`.
- Marker-Parts-Installation gibt weiterhin den Marker zurueck.
- Widget-Bau und oeffentlicher Installer-Einstieg bleiben unveraendert.

## Risiken

- Callback-Reihenfolge im Tuple muss unveraendert bleiben.
- `update_marker`, `start_drag`, `drag` und `end_drag` muessen unveraendert an die Binding-Aktivierung gehen.
- Fehler der Binding-Aktivierung duerfen nicht versehentlich geschluckt werden.
- Die Marker-Parts-Installation darf den Rueckgabewert nicht aendern.

## Performance Vorher

- Commit vorher: `52bd780d`
- Messbedingungen: Dummy-Container, Dummy-Pane, Dummy-Marker, Dummy-Grip, Dummy-Callbacks, Dummy-Aktivator, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_install_parts_current`: best of 5 `159 ns`

## Geplante kleine Aenderung

- Callback-Tuple-Entpackung und Binding-Aktivierung in `_standalone_radio_pane_activate_marker_parts` extrahieren.
- Direkte Tests fuer Aktivierungsargumente und Fehlerpropagation ergaenzen.
- Install-Parts-Test auf Callback-Bau plus Aktivierungsdelegation umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_activate_marker_parts` eingefuehrt.
- `_standalone_radio_pane_install_marker_parts` nutzt den neuen Aktivierungs-Helper.
- Tests fuer Aktivierung, Fehlerpropagation und Install-Parts-Delegation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Callbacks werden weiterhin vor der Binding-Aktivierung gebaut.
- Binding-Aktivierung erhaelt weiterhin Container, Pane, Grip und die vier Callbacks.
- Die Marker-Parts-Installation gibt weiterhin den Marker zurueck.
- Der oeffentliche Installer-Einstieg bleibt unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-parts-activation.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-parts-activation.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_activate_marker_parts_activates_bindings`
- `test_standalone_radio_pane_activate_marker_parts_propagates_activation_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `194 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `196 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2432 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_install_parts_activator_helper`: best of 5 `145 ns`

## Bewertung

- Die Binding-Aktivierung ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Callbacks und Dummy-Aktivatoren statt echter Tk-Bindings.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-parts-activation`.
