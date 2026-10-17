# 13 Radio Marker Initial Update

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: initiales Update-Scheduling fuer den Radio-Pane-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Start des Radio-Tab-Aufbaus

## Abhaengigkeiten und Seiteneffekte

- `container.after(0, update_marker)` bleibt der initiale Update-Weg.
- Fehler beim initialen Scheduling werden weiterhin geschluckt.
- Marker-Geometrie, Drag-State, Event-Bindings und Idle-Scheduling bleiben unveraendert.
- Keine Aenderung an Radio-Start, Detach/Reattach oder Embedded-Panel.

## Risiken

- Das initiale Update muss weiterhin mit Delay `0` geplant werden.
- Fehler beim initialen Scheduling duerfen weiterhin nicht nach aussen gelangen.
- Der Helper darf keine Tk-Widgets erzeugen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `5219ff27`
- Messbedingungen: Dummy-Container mit `after`, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_initial_update`: best of 5 `40 ns`

## Geplante kleine Aenderung

- Initiales `container.after(0, ...)` in `_schedule_initial_radio_pane_marker_update` extrahieren.
- Direkte Tests fuer erfolgreichen `after(0, ...)`-Aufruf und Fehler-Toleranz ergaenzen.
- Marker-Drag-Logik, Update-Scheduling und Pane-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_schedule_initial_radio_pane_marker_update` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer das initiale Marker-Update.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Der Marker wird weiterhin direkt nach Installation aktualisiert.
- Initiale Scheduling-Fehler bleiben toleriert.
- Drag-Handler geben weiterhin `"break"` zurueck.
- Event-Bindings bleiben unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-initial-update.md`
- `docs/refactoring/performance/areas/13-radio-marker-initial-update.md`

## Hinzugefuegte Tests

- `test_schedule_initial_radio_pane_marker_update_uses_after_zero`
- `test_schedule_initial_radio_pane_marker_update_ignores_after_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `160 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `162 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2239 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_initial_update`: best of 5 `59 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Container statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-initial-update`.
