# 13 Radio Marker Schedule Callback

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: lokaler Marker-Schedule-Callback im Pane-Drag-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Callback bindet weiterhin `container`, `drag_state` und den Update-Callback.
- Scheduling erfolgt weiterhin ueber `_request_radio_pane_marker_update`.
- Drag-Callback erhaelt weiterhin denselben Schedule-Callback.
- Update-, Bindings- und Initial-Update-Logik bleiben unveraendert.
- Source-basierter Marker-Kommentar bleibt unveraendert.

## Risiken

- Der Callback muss dieselben Objekte binden wie die lokale Funktion vorher.
- Mehrfache Aufrufe muessen erneut an den Request-Helper delegieren.
- Der Helper darf kein Scheduling vorzeitig ausloesen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `2dac55e6`
- Messbedingungen: Dummy-Container, Dummy-Drag-State, Dummy-Update-Callback und Dummy-Requester, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_schedule_callback`: best of 5 `67 ns`

## Geplante kleine Aenderung

- Marker-Schedule-Callback in `_make_radio_pane_marker_schedule_callback` extrahieren.
- Direkte Tests fuer gebundene Objekte und wiederholte Aufrufe ergaenzen.
- Restlichen Marker-Installer unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_make_radio_pane_marker_schedule_callback` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer den Schedule-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker-Updates werden weiterhin ueber den bestehenden Request-Helper geplant.
- Pending-State-Verhalten bleibt unveraendert.
- Drag-Event plant weiterhin Marker-Updates.
- Fehlerbehandlung beim Scheduling bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-schedule-callback.md`
- `docs/refactoring/performance/areas/13-radio-marker-schedule-callback.md`

## Hinzugefuegte Tests

- `test_make_radio_pane_marker_schedule_callback_binds_update_dependencies`
- `test_make_radio_pane_marker_schedule_callback_invokes_requester_each_time`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `225 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `227 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2304 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_schedule_callback`: best of 5 `152 ns`

## Bewertung

- Der Helper fuegt nur den erwartbaren Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-schedule-callback`.
