# 13 Radio Marker Drag Start Callback

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: lokaler Marker-Drag-Start-Callback im Pane-Drag-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Callback bindet weiterhin `drag_state` und `pane`.
- Drag-Start erfolgt weiterhin ueber `_handle_radio_pane_marker_drag_start`.
- Grip-Binding erhaelt weiterhin denselben Start-Drag-Callback.
- Drag-, End- und Scheduling-Callbacks bleiben unveraendert.
- Source-basierter Marker-Kommentar bleibt unveraendert.

## Risiken

- Der Callback muss dieselben Objekte binden wie die lokale Funktion vorher.
- Event-Argument muss weiterhin an den Handler durchgereicht werden.
- Rueckgabewert des Handlers muss unveraendert durchgereicht werden.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `97983731`
- Messbedingungen: Dummy-Drag-State, Dummy-Pane und Dummy-Handler, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_drag_start_callback`: best of 5 `61 ns`

## Geplante kleine Aenderung

- Marker-Drag-Start-Callback in `_make_radio_pane_marker_drag_start_callback` extrahieren.
- Direkte Tests fuer gebundene Objekte und Rueckgabewert ergaenzen.
- Restlichen Marker-Installer unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_make_radio_pane_marker_drag_start_callback` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer den Start-Drag-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Drag-Start speichert weiterhin Root- und Sash-Position.
- Drag-Start gibt weiterhin `"break"` aus dem bestehenden Handler zurueck.
- Fehlerbehandlung beim Drag-Start bleibt unveraendert.
- Bindings bleiben unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-drag-start-callback.md`
- `docs/refactoring/performance/areas/13-radio-marker-drag-start-callback.md`

## Hinzugefuegte Tests

- `test_make_radio_pane_marker_drag_start_callback_binds_state_event_and_pane`
- `test_make_radio_pane_marker_drag_start_callback_returns_handler_result`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `227 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `229 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2306 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_drag_start_callback`: best of 5 `140 ns`

## Bewertung

- Der Helper fuegt nur den erwartbaren Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-drag-start-callback`.
