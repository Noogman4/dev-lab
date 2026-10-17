# 13 Standalone Radio Marker Drag End

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: End-Drag-Callback des Standalone-Radio-Pane-Markers aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Das Marker-Update wird weiterhin beim Drag-Ende ausgefuehrt.
- Der Drag-End-Handler gibt weiterhin `"break"` zurueck.
- Fehler aus dem Marker-Update werden weiterhin nicht im neuen Helper geschluckt.
- Drag-Start, Drag-Motion, Sash-Positionierung und Bindings bleiben unveraendert.

## Risiken

- Der Rueckgabewert `"break"` muss erhalten bleiben, damit Tk das Event nicht weiterverarbeitet.
- Das Marker-Update muss vor dem Rueckgabewert ausgefuehrt werden.
- Fehlerbehandlung darf nicht versehentlich breiter werden.
- Der lokale Callback muss weiterhin mit optionalem Tk-Event aufrufbar bleiben.

## Performance Vorher

- Commit vorher: `00ee3933`
- Messbedingungen: direkter End-Drag-Pfad mit Dummy-Update-Callback, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_drag_end_inline`: best of 5 `31 ns`

## Geplante kleine Aenderung

- End-Drag-Ablauf in `_standalone_radio_pane_end_drag` extrahieren.
- Direkte Tests fuer Update plus `"break"` und Update-Fehler ergaenzen.
- Lokalen `_end_drag` im Installer auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_end_drag` eingefuehrt.
- Lokaler `_end_drag` delegiert an den neuen Helper.
- Tests fuer erfolgreichen Update-Aufruf und Fehlerdurchreichung ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Start/Drag-Motion-Logik geaendert.

## Unveraendertes Sollverhalten

- Drag-End aktualisiert weiterhin den Marker.
- Drag-End gibt weiterhin `"break"` zurueck.
- Update-Fehler werden weiterhin nicht im End-Drag-Helper abgefangen.
- Die Grip-ButtonRelease-Bindung bleibt unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-drag-end.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-drag-end.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_end_drag_updates_marker_and_breaks`
- `test_standalone_radio_pane_end_drag_propagates_update_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `135 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `137 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2373 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_drag_end_helper`: best of 5 `46 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen Dummy-Callbacks, nicht echte Standalone-Marker-Drag-Bedienung.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-drag-end`.
