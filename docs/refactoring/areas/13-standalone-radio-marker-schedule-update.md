# 13 Standalone Radio Marker Schedule Update

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Scheduling des Standalone-Radio-Pane-Marker-Updates aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- `_install_pane_drag_marker` ruft das Update-Scheduling weiterhin waehrend Drag-Bewegungen auf.
- `_standalone_radio_pane_schedule_marker_update` prueft `update_pending`, setzt es, plant den Runner via `after_idle` und nutzt den bisherigen Immediate-Fallback.
- Der Runner setzt `update_pending` vor dem Update wieder auf `False`.
- Keine Binding- oder Drag-Berechnung wird veraendert.

## Risiken

- Pending-Updates duerfen weiterhin nicht doppelt geplant werden.
- `update_pending` muss weiterhin vor dem geplanten Update auf `True` und im Runner auf `False` gesetzt werden.
- Wenn `after_idle` fehlschlaegt, muss das Update weiterhin sofort laufen.
- Fehler aus dem eigentlichen Update duerfen nicht in diesem Helper geschluckt werden.

## Performance Vorher

- Commit vorher: `66996ba8`
- Messbedingungen: direkter Scheduling-Pfad mit Dummy-Container und Dummy-Update, `timeit.repeat`, 100.000 Wiederholungen
- `standalone_radio_marker_schedule_inline`: best of 5 `142 ns`

## Geplante kleine Aenderung

- Scheduling-Pfad in `_standalone_radio_pane_schedule_marker_update` extrahieren.
- Direkte Tests fuer Pending-Skip, `after_idle`-Runner und Immediate-Fallback ergaenzen.
- Lokalen `_schedule_marker_update` im Installer auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_schedule_marker_update` eingefuehrt.
- Lokaler `_schedule_marker_update` delegiert an den neuen Helper.
- Tests fuer Skip, geplanten Runner und Fallback ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Mehrere parallele Update-Anforderungen bleiben ueber `update_pending` gedrosselt.
- Das geplante Update setzt den Pending-Status vor dem Ausfuehren zurueck.
- Bei `after_idle`-Fehlern laeuft das Update weiterhin sofort.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-schedule-update.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-schedule-update.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_schedule_marker_update_skips_pending_state`
- `test_standalone_radio_pane_schedule_marker_update_uses_after_idle_runner`
- `test_standalone_radio_pane_schedule_marker_update_runs_on_after_idle_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `129 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `132 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2368 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_schedule_helper`: best of 5 `200 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen Dummy-Objekte, nicht echte Standalone-Marker-Drag-Bedienung.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-schedule-update`.
