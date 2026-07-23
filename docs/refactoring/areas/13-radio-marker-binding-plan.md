# 13 Radio Marker Binding Plan

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Zuordnung von Marker-Binding-Widgets zu Event-Bindings
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_bind_radio_pane_marker_callbacks`

## Abhaengigkeiten und Seiteneffekte

- Update-Bindings werden weiterhin ueber `_radio_pane_update_bindings` erzeugt.
- Grip-Bindings werden weiterhin ueber `_radio_pane_grip_bindings` erzeugt.
- Event-Binding erfolgt weiterhin ueber `_bind_radio_pane_marker_events`.
- Binding-Fehler werden weiterhin in `_bind_radio_pane_marker_events` geschluckt.

## Risiken

- Container und Pane muessen weiterhin dieselben Update-Bindings erhalten.
- Grip muss weiterhin Start-, Drag- und End-Bindings erhalten.
- Binding-Reihenfolge darf sich nicht aendern.
- Fehlerverhalten beim Binden darf sich nicht aendern.

## Performance Vorher

- Commit vorher: `b5e0f4e7`
- Messbedingungen: Dummy-Widgets und Dummy-Callbacks, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_binding_plan`: best of 5 `280 ns`

## Geplante kleine Aenderung

- Binding-Zuordnung in `_radio_pane_marker_binding_plan` extrahieren.
- Direkten Test fuer Widget-zu-Bindings-Zuordnung ergaenzen.
- `_bind_radio_pane_marker_callbacks` auf den neuen Plan umstellen.

## Durchgefuehrte Aenderungen

- `_radio_pane_marker_binding_plan` eingefuehrt.
- `_bind_radio_pane_marker_callbacks` iteriert ueber den Plan.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Container erhaelt weiterhin Configure-, Release- und Motion-Update-Bindings.
- Pane erhaelt weiterhin dieselben Update-Bindings.
- Grip erhaelt weiterhin Button-, Motion- und Release-Drag-Bindings.
- Bindings werden weiterhin mit `add="+"` registriert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-binding-plan.md`
- `docs/refactoring/performance/areas/13-radio-marker-binding-plan.md`

## Hinzugefuegte Tests

- `test_radio_pane_marker_binding_plan_maps_widgets_to_bindings`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `243 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `244 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2321 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_binding_plan`: best of 5 `308 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-binding-plan`.
