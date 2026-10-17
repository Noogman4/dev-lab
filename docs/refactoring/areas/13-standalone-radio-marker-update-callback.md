# 13 Standalone Radio Marker Update Callback

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: gebundenen Marker-Update-Callback fuer den Standalone-Radio-Pane-Marker aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Marker-Update laeuft weiterhin ueber `_standalone_radio_pane_update_marker_safe`.
- Der neue Helper bindet nur Pane, Place-Callback und Marker.
- Der Callback akzeptiert weiterhin optional ein Tk-Event-Argument.
- Safe-Forget-Verhalten bleibt im bestehenden Safe-Helper.

## Risiken

- Callback muss Pane, Place-Callback und Marker unveraendert weiterreichen.
- Event-Argumente aus Tk-Bindings duerfen den Aufruf nicht stoeren.
- Fehler des injizierten Update-Helpers duerfen im Callback nicht versehentlich geschluckt werden.
- Marker-Place, Drag-Motion und Scheduling duerfen unveraendert bleiben.

## Performance Vorher

- Commit vorher: `a0e5bb5f`
- Messbedingungen: Dummy-Pane, Dummy-Place-Callback, Dummy-Marker, Dummy-Update-Helper, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_update_callback_inline`: best of 5 `226 ns`

## Geplante kleine Aenderung

- Lokalen `_update_marker`-Wrapper in `_standalone_radio_pane_update_callback` extrahieren.
- Direkte Tests fuer gebundene Marker-Kontextargumente, Event-Toleranz und Fehlerpropagation ergaenzen.
- Restlichen Marker-Installer unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_update_callback` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer den Marker-Update-Callback.
- Tests fuer gebundene Argumente, Event-Toleranz und Fehlerpropagation ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Update liest weiterhin den aktuellen Sash ueber `_standalone_radio_pane_update_marker`.
- Safe-Update vergisst den Marker weiterhin bei Update-Fehlern.
- Configure-, ButtonRelease- und Motion-Bindings nutzen weiterhin denselben Update-Callback.
- Drag-Motion setzt, platziert und scheduled weiterhin in derselben Reihenfolge.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-update-callback.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-update-callback.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_update_callback_binds_marker_context_and_event`
- `test_standalone_radio_pane_update_callback_propagates_update_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `164 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `166 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2402 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_update_callback_helper`: best of 5 `257 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-update-callback`.
