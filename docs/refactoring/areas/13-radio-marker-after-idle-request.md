# 13 Radio Marker After Idle Request

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: `after_idle`-Request fuer geplante Pane-Drag-Marker-Updates
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_schedule_radio_pane_marker_update`

## Abhaengigkeiten und Seiteneffekte

- Der Update-Runner wird weiterhin ueber `_make_radio_pane_marker_update_runner` erzeugt.
- `after_idle` bleibt weiterhin der bevorzugte Scheduling-Weg.
- Bei `after_idle`-Fehlern laeuft der Runner weiterhin sofort.
- Pending-, Drag-, Binding- und Marker-Placement-Verhalten bleiben unveraendert.

## Risiken

- Erfolgreicher `after_idle`-Request darf den Runner nicht direkt ausfuehren.
- Fehlerhafter `after_idle`-Request muss weiterhin den Runner sofort ausfuehren.
- Pending-Update-Verhalten darf sich nicht aendern.
- Bestehende Scheduling-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `20bd057e`
- Messbedingungen: Dummy-Container mit `after_idle` und Dummy-Runner, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_after_idle_request`: best of 5 `38 ns`

## Geplante kleine Aenderung

- `after_idle`-Request mit Fallback in `_request_radio_pane_marker_after_idle` extrahieren.
- Direkte Tests fuer Erfolgs- und Fehlerpfad ergaenzen.
- `_schedule_radio_pane_marker_update` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_request_radio_pane_marker_after_idle` eingefuehrt.
- `_schedule_radio_pane_marker_update` uebergibt den erzeugten Runner an den Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Pending-Updates werden weiterhin nicht doppelt geplant.
- Neue Updates setzen `update_pending` weiterhin vor dem Scheduling auf `True`.
- Erfolgreiches `after_idle` plant weiterhin den Runner.
- Bei `after_idle`-Fehlern laeuft der Runner weiterhin sofort.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-after-idle-request.md`
- `docs/refactoring/performance/areas/13-radio-marker-after-idle-request.md`

## Hinzugefuegte Tests

- `test_request_radio_pane_marker_after_idle_schedules_runner`
- `test_request_radio_pane_marker_after_idle_runs_on_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `247 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `249 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2326 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen; der Eskalationslauf ausserhalb der Sandbox wurde vom Approval-System abgelehnt

## Performance Nachher

- `radio_marker_after_idle_request`: best of 5 `63 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke konnte in diesem Schritt nicht erfolgreich wiederholt werden.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-after-idle-request`.
