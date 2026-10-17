# 13 Standalone Radio Marker Binding Plan

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Zuordnung von Standalone-Radio-Pane-Marker-Widgets zu Event-Bindings aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Update-Bindings werden weiterhin ueber `_standalone_radio_pane_update_bindings` erzeugt.
- Grip-Bindings werden weiterhin ueber `_standalone_radio_pane_grip_bindings` erzeugt.
- Event-Binding erfolgt weiterhin ueber `_standalone_radio_pane_bind_marker_events`.
- Binding-Fehler werden weiterhin im bestehenden Bind-Helper geschluckt.

## Risiken

- Container und Pane muessen weiterhin dieselben Update-Bindings erhalten.
- Grip muss weiterhin Start-, Drag- und End-Bindings erhalten.
- Binding-Reihenfolge darf sich nicht aendern.
- Fehlerverhalten beim Binden darf sich nicht aendern.

## Performance Vorher

- Commit vorher: `58928378`
- Messbedingungen: direkter Binding-Plan mit Dummy-Widgets und Dummy-Bindings, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_binding_plan_inline`: best of 5 `58 ns`

## Geplante kleine Aenderung

- Binding-Zuordnung in `_standalone_radio_pane_marker_binding_plan` extrahieren.
- Direkten Test fuer Widget-zu-Bindings-Zuordnung ergaenzen.
- `_install_pane_drag_marker` auf den neuen Plan umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_binding_plan` eingefuehrt.
- `_install_pane_drag_marker` iteriert ueber den Plan.
- Test fuer Container-, Pane- und Grip-Zuordnung ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Container erhaelt weiterhin Configure-, Release- und Motion-Update-Bindings.
- Pane erhaelt weiterhin dieselben Update-Bindings.
- Grip erhaelt weiterhin Button-, Motion- und Release-Drag-Bindings.
- Bindings werden weiterhin mit `add="+"` registriert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-binding-plan.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-binding-plan.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_binding_plan_maps_widgets_to_bindings`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `151 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `152 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2388 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_binding_plan_helper`: best of 5 `96 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-binding-plan`.
