# 13 Radio Marker Update Event

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Update-Event-Adapter fuer den Radio-Pane-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Configure-, ButtonRelease- und Motion-Update-Bindings

## Abhaengigkeiten und Seiteneffekte

- Das optionale Tk-Event wird weiterhin ignoriert.
- Das Marker-Update laeuft weiterhin ueber `_update_radio_pane_marker_from_sash`.
- Fehler beim Lesen oder Platzieren fuehren weiterhin zu `place_forget`.
- Marker-Erzeugung, Drag-Callbacks, Bindings und Initial-Update bleiben unveraendert.

## Risiken

- Der Event-Parameter darf das Verhalten nicht beeinflussen.
- Die bestehende Fehlerbehandlung in `_update_radio_pane_marker_from_sash` muss erhalten bleiben.
- Der Helper darf keine neuen Tk-Widgets erzeugen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `4b6ed096`
- Messbedingungen: Dummy-Pane, Dummy-Callback, Marker-Objekt und Dummy-Event, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_update_event`: best of 5 `85 ns`

## Geplante kleine Aenderung

- Update-Event-Adapter in `_handle_radio_pane_marker_update_event` extrahieren.
- Direkte Tests fuer ignoriertes Event und Fehler-Fallback ergaenzen.
- Lokale Callback-Signatur und Binding-Verhalten unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_handle_radio_pane_marker_update_event` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper im internen Update-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Marker-Update liest weiterhin die aktuelle Sash-Position.
- Marker wird weiterhin fuer diese Sash-Position platziert.
- Fehler fuehren weiterhin zum Vergessen des Markers.
- Update-Callback liefert weiterhin keinen speziellen Tk-Rueckgabewert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-update-event.md`
- `docs/refactoring/performance/areas/13-radio-marker-update-event.md`

## Hinzugefuegte Tests

- `test_handle_radio_pane_marker_update_event_ignores_event_and_places_sash`
- `test_handle_radio_pane_marker_update_event_forgets_marker_on_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `186 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `188 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2265 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_update_event`: best of 5 `104 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Panes und Dummy-Callbacks statt echter Tk-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Marker-Aktualisierung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-update-event`.
