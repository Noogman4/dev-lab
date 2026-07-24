# 13 Standalone Radio Marker Drag Start Event

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Drag-Start-Event-Callback des Standalone-Radio-Pane-Markers aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Der Drag-Start-Event-Handler ruft weiterhin die bestehende Start-State-Logik auf.
- Der Handler gibt weiterhin `"break"` zurueck.
- Fehlerbehandlung bleibt in `_standalone_radio_pane_start_drag`.
- Drag-Motion, Drag-End, Sash-Setzen, Marker-Platzierung und Scheduling bleiben unveraendert.

## Risiken

- Der Rueckgabewert `"break"` muss erhalten bleiben, damit Tk das Event nicht weiterverarbeitet.
- Die Start-State-Abhaengigkeiten muessen unveraendert weitergereicht werden.
- Fehlerbehandlung darf nicht versehentlich in den Event-Wrapper verschoben werden.
- Der lokale `_start_drag`-Callback muss weiterhin mit einem Tk-Event aufrufbar bleiben.

## Performance Vorher

- Commit vorher: `eab9826b`
- Messbedingungen: direkter Drag-Start-Event-Wrapper mit Dummy-State, Dummy-Event und Dummy-Pane, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_drag_start_event_inline`: best of 5 `129 ns`

## Geplante kleine Aenderung

- Drag-Start-Event-Wrapper in `_standalone_radio_pane_start_drag_event` extrahieren.
- Direkte Tests fuer State-Write plus `"break"` und Fehlerdurchreichung bei injiziertem Start-Helper ergaenzen.
- Lokalen `_start_drag` im Installer auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_start_drag_event` eingefuehrt.
- Lokaler `_start_drag` delegiert an den neuen Helper.
- Tests fuer erfolgreichen Start-State-Write und Fehlerdurchreichung ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Motion/Drag-End-Logik geaendert.

## Unveraendertes Sollverhalten

- Drag-Start speichert weiterhin Root-Y und Sash-Y ueber die bestehende Start-State-Logik.
- Der Tk-Eventfluss wird weiterhin durch `"break"` gestoppt.
- Fehler-Fallback fuer normale Start-State-Fehler bleibt in `_standalone_radio_pane_start_drag`.
- Die Grip-Button-1-Bindung bleibt unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-drag-start-event.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-drag-start-event.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_start_drag_event_records_state_and_breaks`
- `test_standalone_radio_pane_start_drag_event_propagates_start_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `139 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `141 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2377 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_drag_start_event_helper`: best of 5 `161 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen Dummy-Objekte, nicht echte Standalone-Marker-Drag-Bedienung.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-drag-start-event`.
