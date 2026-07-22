# 13 Radio Marker Drag Motion

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Drag-Motion-Ablauf fuer den Radio-Pane-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Grip-Drag-Callback

## Abhaengigkeiten und Seiteneffekte

- Ziel-Sash wird weiterhin aus Event und Drag-State berechnet.
- Sash-Position wird weiterhin gesetzt.
- Marker wird weiterhin fuer die neue Sash-Position platziert.
- Marker-Update wird weiterhin geplant.
- Fehler im Drag-Motion-Ablauf werden weiterhin geschluckt.

## Risiken

- Die Reihenfolge `target -> sash setzen -> marker platzieren -> update planen` muss erhalten bleiben.
- Fehler duerfen den Tk-Callback weiterhin nicht verlassen.
- Der Helper darf keine Tk-Widgets erzeugen.
- Der Event-Handler muss weiterhin `"break"` zurueckgeben.

## Performance Vorher

- Commit vorher: `4678dc70`
- Messbedingungen: Dummy-Event, Dummy-Pane, Dict-State und Dummy-Callbacks, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_drag_motion`: best of 5 `262 ns`

## Geplante kleine Aenderung

- Drag-Motion-Ablauf in `_handle_radio_pane_marker_drag` extrahieren.
- Direkte Tests fuer Erfolgsweg, Zielberechnungsfehler und Place-Fehler ergaenzen.
- Tk-Event-Handler, Bindings und Rueckgabewert unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_handle_radio_pane_marker_drag` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper im internen Drag-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Drag-Bewegung setzt weiterhin die Sash-Position.
- Marker wird weiterhin sofort fuer die neue Position platziert.
- Marker-Update wird weiterhin geplant.
- Drag-Handler gibt weiterhin `"break"` zurueck.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-drag-motion.md`
- `docs/refactoring/performance/areas/13-radio-marker-drag-motion.md`

## Hinzugefuegte Tests

- `test_handle_radio_pane_marker_drag_sets_sash_places_marker_and_schedules`
- `test_handle_radio_pane_marker_drag_ignores_target_failures`
- `test_handle_radio_pane_marker_drag_ignores_place_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `171 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `174 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2251 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_drag_motion`: best of 5 `309 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Events und Dummy-Panes statt echter Tk-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Drag-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-drag-motion`.
