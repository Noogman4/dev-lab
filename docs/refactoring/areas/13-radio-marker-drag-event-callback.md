# 13 Radio Marker Drag Event Callback

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: lokaler Marker-Drag-Event-Callback im Pane-Drag-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Callback bindet weiterhin `drag_state`, `pane`, Platzierungs-Callback und Schedule-Callback.
- Drag-Motion erfolgt weiterhin ueber `_handle_radio_pane_marker_drag_event`.
- Grip-Binding erhaelt weiterhin denselben Drag-Callback.
- Start-, End-, Update- und Scheduling-Callbacks bleiben unveraendert.
- Source-basierter Marker-Kommentar bleibt unveraendert.

## Risiken

- Der Callback muss dieselben Objekte binden wie die lokale Funktion vorher.
- Event-Argument muss weiterhin an den Handler durchgereicht werden.
- Rueckgabewert des Handlers muss unveraendert durchgereicht werden.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `bfd5cffc`
- Messbedingungen: Dummy-Drag-State, Dummy-Pane, Dummy-Callbacks und Dummy-Handler, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_drag_event_callback`: best of 5 `63 ns`

## Geplante kleine Aenderung

- Marker-Drag-Event-Callback in `_make_radio_pane_marker_drag_event_callback` extrahieren.
- Direkte Tests fuer gebundene Objekte und Rueckgabewert ergaenzen.
- Restlichen Marker-Installer unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_make_radio_pane_marker_drag_event_callback` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer den Drag-Event-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Drag-Motion berechnet weiterhin die neue Sash-Position.
- Marker wird weiterhin waehrend des Drags platziert.
- Marker-Update wird weiterhin nach dem Drag geplant.
- Handler-Rueckgabe bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-drag-event-callback.md`
- `docs/refactoring/performance/areas/13-radio-marker-drag-event-callback.md`

## Hinzugefuegte Tests

- `test_make_radio_pane_marker_drag_event_callback_binds_drag_dependencies`
- `test_make_radio_pane_marker_drag_event_callback_returns_handler_result`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `229 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `231 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2308 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_drag_event_callback`: best of 5 `174 ns`

## Bewertung

- Der Helper fuegt nur den erwartbaren Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-drag-event-callback`.
