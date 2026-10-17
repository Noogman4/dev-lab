# 13 Radio Marker Drag Event

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Motion-Event-Callback fuer den Radio-Pane-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Grip-B1-Motion-Callback

## Abhaengigkeiten und Seiteneffekte

- Die Drag-Motion-Logik laeuft weiterhin ueber `_handle_radio_pane_marker_drag`.
- Der Motion-Handler gibt weiterhin `"break"` zurueck.
- Fehler in der Motion-Logik werden weiterhin im inneren Drag-Helper geschluckt.
- Drag-Start, Drag-End, Sash-Positionierung und Bindings bleiben unveraendert.

## Risiken

- Der Rueckgabewert `"break"` muss auch nach ignorierten Motion-Fehlern erhalten bleiben.
- Die Reihenfolge `target -> sash setzen -> marker platzieren -> update planen` darf sich nicht aendern.
- Die Fehlerbehandlung darf nicht versehentlich aus dem inneren Helper herausgezogen werden.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `7efe63be`
- Messbedingungen: Dummy-Event, Dummy-Pane, Dict-State und Dummy-Callbacks, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_drag_event`: best of 5 `294 ns`

## Geplante kleine Aenderung

- Motion-Event-Wrapper in `_handle_radio_pane_marker_drag_event` extrahieren.
- Direkte Tests fuer Erfolgsweg plus `"break"` und ignorierten Motion-Fehler plus `"break"` ergaenzen.
- Bindings und lokale Callback-Signatur unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_handle_radio_pane_marker_drag_event` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper im internen Motion-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Drag-Motion setzt weiterhin die Sash-Position.
- Marker wird weiterhin sofort fuer die neue Position platziert.
- Marker-Update wird weiterhin geplant.
- Motion-Handler gibt weiterhin `"break"` zurueck.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-drag-event.md`
- `docs/refactoring/performance/areas/13-radio-marker-drag-event.md`

## Hinzugefuegte Tests

- `test_handle_radio_pane_marker_drag_event_handles_motion_and_breaks`
- `test_handle_radio_pane_marker_drag_event_breaks_after_ignored_motion_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `182 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `184 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2261 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_drag_event`: best of 5 `327 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Events und Dummy-Panes statt echter Tk-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Drag-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-drag-event`.
