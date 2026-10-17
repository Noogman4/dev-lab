# 13 Standalone Radio Marker Drag Event

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Drag-Event-Callback des Standalone-Radio-Pane-Markers aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Der Drag-Event-Handler ruft weiterhin die Drag-Motion-Logik auf.
- Fehler waehrend der Drag-Motion werden weiterhin geschluckt.
- Der Handler gibt weiterhin immer `"break"` zurueck.
- Drag-Start, Drag-End, Sash-Setzen, Marker-Platzierung und Scheduling bleiben unveraendert.

## Risiken

- Fehler im Motion-Pfad duerfen den Tk-Eventfluss weiterhin nicht abbrechen.
- Der Rueckgabewert `"break"` muss auch nach Fehlern erhalten bleiben.
- Die Abhaengigkeiten muessen unveraendert an die Motion-Logik weitergereicht werden.
- Der lokale `_drag`-Callback muss weiterhin mit einem Tk-Event aufrufbar bleiben.

## Performance Vorher

- Commit vorher: `5398c2aa`
- Messbedingungen: direkter Drag-Event-Wrapper mit Dummy-State, Dummy-Event und No-op-nahem Callback-Pfad, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_drag_event_inline`: best of 5 `191 ns`

## Geplante kleine Aenderung

- Drag-Event-Wrapper in `_standalone_radio_pane_drag_event` extrahieren.
- Direkte Tests fuer Erfolgsweg und geschluckten Motion-Fehler ergaenzen.
- Lokalen `_drag` im Installer auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_drag_event` eingefuehrt.
- Lokaler `_drag` delegiert an den neuen Helper.
- Tests fuer normalen Motion-Aufruf und Fehlerpfad ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Motion-Rechnung geaendert.

## Unveraendertes Sollverhalten

- Drag-Event verschiebt weiterhin Sash und Marker ueber die bestehende Motion-Logik.
- Fehler im Motion-Pfad werden weiterhin ignoriert.
- Der Tk-Eventfluss wird weiterhin durch `"break"` gestoppt.
- Marker-Scheduling bleibt unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-drag-event.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-drag-event.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_drag_event_handles_motion_and_breaks`
- `test_standalone_radio_pane_drag_event_breaks_after_ignored_motion_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `137 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `139 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2375 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_drag_event_helper`: best of 5 `387 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen Dummy-Callbacks, nicht echte Standalone-Marker-Drag-Bedienung.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-drag-event`.
