# 13 Radio Marker Update Callback

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: lokaler Marker-Update-Callback im Pane-Drag-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Callback bindet weiterhin `pane`, Platzierungs-Callback und `marker`.
- Update erfolgt weiterhin ueber `_handle_radio_pane_marker_update_event`.
- Bindings und Initial-Update erhalten weiterhin denselben Update-Callback.
- Drag- und Scheduling-Callbacks bleiben unveraendert.
- Source-basierter Marker-Kommentar bleibt unveraendert.

## Risiken

- Der Callback muss dieselben Objekte binden wie die lokale Funktion vorher.
- Event-Argument muss weiterhin optional sein und `None` als Standard nutzen.
- Der Helper darf kein Update vorzeitig ausloesen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `37e78719`
- Messbedingungen: Dummy-Pane, Dummy-Place-Callback, Dummy-Marker und Dummy-Handler, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_update_callback`: best of 5 `72 ns`

## Geplante kleine Aenderung

- Marker-Update-Callback in `_make_radio_pane_marker_update_callback` extrahieren.
- Direkte Tests fuer gebundene Objekte und Default-Event ergaenzen.
- Restlichen Marker-Installer unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_make_radio_pane_marker_update_callback` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer den Update-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker-Update fragt weiterhin die aktuelle Sash-Position ab.
- Marker wird weiterhin ueber den bestehenden Platzierungs-Callback positioniert.
- Fehlerbehandlung beim Update bleibt unveraendert.
- Bindings und Initial-Update bleiben unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-update-callback.md`
- `docs/refactoring/performance/areas/13-radio-marker-update-callback.md`

## Hinzugefuegte Tests

- `test_make_radio_pane_marker_update_callback_binds_update_dependencies`
- `test_make_radio_pane_marker_update_callback_defaults_event_to_none`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `223 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `225 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2302 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_update_callback`: best of 5 `162 ns`

## Bewertung

- Der Helper fuegt nur den erwartbaren Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-update-callback`.
