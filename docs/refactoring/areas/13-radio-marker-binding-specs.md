# 13 Radio Marker Binding Specs

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Event-Binding-Spezifikationen fuer Radio-Pane-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Container-/Pane-Bindings und Grip-Bindings

## Abhaengigkeiten und Seiteneffekte

- Container und Pane behalten `Configure`, `ButtonRelease-1` und `B1-Motion`.
- Grip behaelt `Button-1`, `B1-Motion` und `ButtonRelease-1`.
- Callback-Zuordnung bleibt unveraendert.
- `add="+"` bleibt im bestehenden Bind-Helper unveraendert.
- Keine Aenderung an Radio-Start, Detach/Reattach oder Embedded-Panel.

## Risiken

- Event-Namen muessen exakt erhalten bleiben.
- Callback-Reihenfolge muss unveraendert bleiben.
- Der Helper darf keine Tk-Widgets erzeugen.
- Keine Aenderung an Drag-Rueckgabewerten.

## Performance Vorher

- Commit vorher: `55e44588`
- Messbedingungen: direkte Tuple-Literale mit Dummy-Callbacks, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_binding_specs`: best of 5 `126 ns`

## Geplante kleine Aenderung

- Update-Bindings in `_radio_pane_update_bindings` extrahieren.
- Grip-Bindings in `_radio_pane_grip_bindings` extrahieren.
- Direkte Tests fuer Event-Namen und Callback-Identitaet ergaenzen.
- Binding-Ausfuehrung, Marker-Drag-Logik und Pane-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_radio_pane_update_bindings` eingefuehrt.
- `_radio_pane_grip_bindings` eingefuehrt.
- `_install_pane_drag_marker` nutzt beide Helper beim Binden der Marker-Events.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Container und Pane erhalten weiterhin dieselben Update-Events.
- Grip erhaelt weiterhin dieselben Drag-Events.
- Bind-Fehler bleiben im bestehenden Bind-Helper toleriert.
- Drag-Handler geben weiterhin `"break"` zurueck.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-binding-specs.md`
- `docs/refactoring/performance/areas/13-radio-marker-binding-specs.md`

## Hinzugefuegte Tests

- `test_radio_pane_update_bindings_use_update_callback_for_all_events`
- `test_radio_pane_grip_bindings_use_drag_callbacks`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `169 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `171 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2248 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_binding_specs`: best of 5 `160 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen Tuple-Spezifikationen ohne echte Tk-Bindings.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-binding-specs`.
