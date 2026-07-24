# 13 Standalone Radio Marker Schedule Callback

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: gebundenen Marker-Schedule-Callback fuer den Standalone-Radio-Pane-Marker aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Scheduling laeuft weiterhin ueber `_standalone_radio_pane_schedule_marker_update`.
- Der neue Helper bindet nur Container, Drag-State und Update-Callback.
- Pending-State-Logik und `after_idle`-Fallback bleiben im bestehenden Scheduler.
- Drag-Motion ruft weiterhin einen einfachen `schedule_marker_update()`-Callback auf.

## Risiken

- Callback muss Container, Drag-State und Update-Callback unveraendert weiterreichen.
- Fehler des injizierten Schedulers duerfen im Callback nicht versehentlich geschluckt werden.
- Pending-State-Verhalten darf nicht veraendert werden.
- Drag-Rechnung, Marker-Place und Update duerfen unveraendert bleiben.

## Performance Vorher

- Commit vorher: `38957740`
- Messbedingungen: Dummy-Container, Dummy-State, Dummy-Update-Callback, Dummy-Scheduler, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_schedule_callback_inline`: best of 5 `222 ns`

## Geplante kleine Aenderung

- Lokalen `_schedule_marker_update`-Wrapper in `_standalone_radio_pane_schedule_callback` extrahieren.
- Direkte Tests fuer gebundene Scheduling-Kontextargumente und Fehlerpropagation ergaenzen.
- Restlichen Marker-Installer unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_schedule_callback` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer den Marker-Schedule-Callback.
- Tests fuer gebundene Argumente und Fehlerpropagation ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Pending Updates werden weiterhin uebersprungen.
- Erfolgreiches Scheduling nutzt weiterhin `container.after_idle`.
- Bei `after_idle`-Fehlern laeuft der Update-Runner weiterhin direkt.
- Drag-Motion setzt, platziert und scheduled weiterhin in derselben Reihenfolge.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-schedule-callback.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-schedule-callback.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_schedule_callback_binds_update_context`
- `test_standalone_radio_pane_schedule_callback_propagates_schedule_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `166 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `168 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2404 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_schedule_callback_helper`: best of 5 `287 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-schedule-callback`.
