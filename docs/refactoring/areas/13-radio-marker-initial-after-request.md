# 13 Radio Marker Initial After Request

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Initialer `after(0)`-Request fuer den Pane-Drag-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_schedule_initial_radio_pane_marker_update`

## Abhaengigkeiten und Seiteneffekte

- Initial-Scheduling erfolgt weiterhin ueber `_schedule_initial_radio_pane_marker_update`.
- `container.after(0, update_marker)` bleibt weiterhin der bevorzugte Weg.
- Fehler beim Initial-Request werden weiterhin geschluckt.
- Binding-, Drag- und Marker-Placement-Verhalten bleiben unveraendert.

## Risiken

- Erfolgreicher Initial-Request muss weiterhin mit Delay `0` geplant werden.
- Fehlerhafter Initial-Request darf weiterhin nicht propagieren.
- Aktivierung muss weiterhin den gleichen Initial-Scheduling-Pfad nutzen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `ae77921d`
- Messbedingungen: Dummy-Container mit `after` und Dummy-Callback, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_initial_after_request`: best of 5 `39 ns`

## Geplante kleine Aenderung

- Initialen `after(0)`-Request in `_request_initial_radio_pane_marker_update` extrahieren.
- Direkte Tests fuer Erfolgs- und Fehlerpfad auf den neuen Helper umstellen.
- `_schedule_initial_radio_pane_marker_update` als Delegation absichern.

## Durchgefuehrte Aenderungen

- `_request_initial_radio_pane_marker_update` eingefuehrt.
- `_schedule_initial_radio_pane_marker_update` delegiert an den neuen Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Initial-Update wird weiterhin mit `after(0, update_marker)` geplant.
- Fehler beim Initial-Scheduling werden weiterhin geschluckt.
- Marker-Aktivierung plant weiterhin ein initiales Update.
- Radio-Tab-Aufbau bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-initial-after-request.md`
- `docs/refactoring/performance/areas/13-radio-marker-initial-after-request.md`

## Hinzugefuegte Tests

- `test_schedule_initial_radio_pane_marker_update_delegates_request`

## Angepasste Tests

- `test_request_initial_radio_pane_marker_update_uses_after_zero`
- `test_request_initial_radio_pane_marker_update_ignores_after_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `251 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `252 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2329 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_initial_after_request`: best of 5 `63 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-initial-after-request`.
