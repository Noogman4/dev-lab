# 13 Radio Marker Schedule Update

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Scheduling fuer Radio-Pane-Marker-Updates
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Drag-Bewegung des Radio-Pane-Markers

## Abhaengigkeiten und Seiteneffekte

- `update_pending` verhindert weiterhin doppelte geplante Updates.
- `update_pending` wird vor dem geplanten Update weiterhin auf `True` gesetzt.
- Der geplante Callback setzt `update_pending` weiterhin vor dem Update wieder auf `False`.
- `container.after_idle(...)` bleibt der bevorzugte Weg.
- Wenn `after_idle` fehlschlaegt, wird das Update weiterhin sofort ausgefuehrt.

## Risiken

- Pending-Updates duerfen weiterhin nicht mehrfach geplant werden.
- Der Fallback muss den Pending-Status wieder zuruecksetzen.
- Der Helper darf keine Tk-Widgets erzeugen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `27fbffd4`
- Messbedingungen: Dummy-Container mit `after_idle`, Drag-State-Dict, `timeit.repeat`, 100.000 Wiederholungen
- `radio_marker_schedule_update`: best of 5 `124 ns`

## Geplante kleine Aenderung

- Update-Scheduling in `_schedule_radio_pane_marker_update` extrahieren.
- Direkte Tests fuer Pending-Skip, `after_idle`-Callback und Fallback ergaenzen.
- Marker-Platzierung, Drag-Handler und Pane-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_schedule_radio_pane_marker_update` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper im internen Scheduler.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Bereits geplante Marker-Updates werden weiterhin uebersprungen.
- Neue Updates werden weiterhin per `after_idle` geplant.
- Bei `after_idle`-Fehlern wird weiterhin sofort aktualisiert.
- Drag-Handler geben weiterhin `"break"` zurueck.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-schedule-update.md`
- `docs/refactoring/performance/areas/13-radio-marker-schedule-update.md`

## Hinzugefuegte Tests

- `test_schedule_radio_pane_marker_update_skips_pending_update`
- `test_schedule_radio_pane_marker_update_uses_after_idle_callback`
- `test_schedule_radio_pane_marker_update_runs_immediately_on_after_idle_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `157 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `160 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --quiet netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: wegen Black-Timeout abgebrochen

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2237 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_schedule_update`: best of 5 `174 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Container statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-schedule-update`.
