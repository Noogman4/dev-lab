# 13 Radio Marker Callbacks Activate

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Binding und initiales Update der Pane-Drag-Marker-Callbacks
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Callback-Binding erfolgt weiterhin ueber `_bind_radio_pane_marker_callbacks`.
- Initiales Marker-Update erfolgt weiterhin ueber `_schedule_initial_radio_pane_marker_update`.
- Binding passiert weiterhin vor dem initialen Update.
- Alle erzeugten Marker-Callbacks bleiben unveraendert.
- Source-basierter Marker-Kommentar bleibt unveraendert.

## Risiken

- Binding und initiales Update muessen in derselben Reihenfolge laufen.
- Initiales Update muss denselben Update-Callback erhalten.
- Binding-Fehler duerfen nicht versehentlich verschluckt werden.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `1fdf0baf`
- Messbedingungen: Dummy-Widgets, Dummy-Callbacks, Dummy-Binder und Dummy-Scheduler, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_callbacks_activate`: best of 5 `60 ns`

## Geplante kleine Aenderung

- Binding plus initiales Update in `_activate_radio_pane_marker_callbacks` extrahieren.
- Direkte Tests fuer Reihenfolge, gebundene Argumente und Fehlerpropagation ergaenzen.
- Restlichen Marker-Installer unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_activate_radio_pane_marker_callbacks` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer Binding und initiales Update.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Container, Pane und Grip werden weiterhin mit denselben Callbacks gebunden.
- Initiales Marker-Update wird weiterhin nach dem Binding geplant.
- Marker-Install gibt weiterhin den Marker zurueck.
- Fehlerverhalten der Binder bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-callbacks-activate.md`
- `docs/refactoring/performance/areas/13-radio-marker-callbacks-activate.md`

## Hinzugefuegte Tests

- `test_activate_radio_pane_marker_callbacks_binds_then_schedules_initial_update`
- `test_activate_radio_pane_marker_callbacks_propagates_binding_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `233 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `235 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2312 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_callbacks_activate`: best of 5 `117 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-callbacks-activate`.
