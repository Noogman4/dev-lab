# 13 Standalone Radio Marker Binding Specs

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Event-Binding-Spezifikationen fuer Standalone-Radio-Pane-Marker aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Container und Pane behalten `Configure`, `ButtonRelease-1` und `B1-Motion`.
- Grip behaelt `Button-1`, `B1-Motion` und `ButtonRelease-1`.
- Callback-Zuordnung bleibt unveraendert.
- `add="+"` bleibt im bestehenden Bind-Helper unveraendert.

## Risiken

- Event-Namen muessen exakt erhalten bleiben.
- Callback-Reihenfolge muss unveraendert bleiben.
- Die Helper duerfen keine Tk-Widgets erzeugen.
- Binding-Fehler muessen weiterhin im bestehenden Bind-Helper behandelt werden.

## Performance Vorher

- Commit vorher: `ba2266f8`
- Messbedingungen: direkte Tuple-Literale mit Dummy-Callbacks, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_binding_specs_inline`: best of 5 `126 ns`

## Geplante kleine Aenderung

- Update-Bindings in `_standalone_radio_pane_update_bindings` extrahieren.
- Grip-Bindings in `_standalone_radio_pane_grip_bindings` extrahieren.
- Direkte Tests fuer Event-Namen und Callback-Identitaet ergaenzen.
- Binding-Ausfuehrung, Marker-Drag-Logik und Pane-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_update_bindings` eingefuehrt.
- `_standalone_radio_pane_grip_bindings` eingefuehrt.
- `_install_pane_drag_marker` nutzt beide Helper beim Binden der Marker-Events.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Container und Pane erhalten weiterhin dieselben Update-Events.
- Grip erhaelt weiterhin dieselben Drag-Events.
- Bind-Fehler bleiben im bestehenden Bind-Helper toleriert.
- Drag-Handler geben weiterhin `"break"` zurueck.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-binding-specs.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-binding-specs.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_update_bindings_use_update_callback_for_all_events`
- `test_standalone_radio_pane_grip_bindings_use_drag_callbacks`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `149 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `151 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2387 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_binding_specs_helper`: best of 5 `150 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen Tuple-Spezifikationen ohne echte Tk-Bindings.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-binding-specs`.
