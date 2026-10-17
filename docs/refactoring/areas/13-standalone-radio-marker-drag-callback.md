# 13 Standalone Radio Marker Drag Callback

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: gebundenen Drag-Callback fuer den Standalone-Radio-Pane-Marker aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Drag-Event laeuft weiterhin ueber `_standalone_radio_pane_drag_event`.
- Der neue Helper bindet nur Drag-State, Sash-Setter, Place-Callback und Schedule-Callback.
- Der Callback akzeptiert weiterhin das Tk-Event-Argument.
- Fehlerbehandlung bleibt im bestehenden Drag-Event-Helper.

## Risiken

- Callback muss Drag-State, Event und alle drei Drag-Abhaengigkeiten unveraendert weiterreichen.
- Rueckgabewert `"break"` muss erhalten bleiben.
- Fehler des injizierten Drag-Event-Helpers duerfen im Callback nicht versehentlich geschluckt werden.
- Drag-Rechnung, Marker-Place und Scheduling duerfen unveraendert bleiben.

## Performance Vorher

- Commit vorher: `f786f909`
- Messbedingungen: Dummy-State, Dummy-Event, Dummy-Callbacks, Dummy-Drag-Event-Helper, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_drag_callback_inline`: best of 5 `249 ns`

## Geplante kleine Aenderung

- Lokalen `_drag`-Wrapper in `_standalone_radio_pane_drag_callback` extrahieren.
- Direkte Tests fuer gebundene Drag-Argumente, Rueckgabewert und Fehlerpropagation ergaenzen.
- Restlichen Marker-Installer unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_drag_callback` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer den Drag-Callback.
- Tests fuer gebundene Argumente, Rueckgabewert und Fehlerpropagation ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Drag-Motion berechnet weiterhin `new_sash` aus Start-Sash und Pointer-Delta.
- Drag-Motion setzt, platziert und scheduled weiterhin in derselben Reihenfolge.
- Drag-Event toleriert Motion-Fehler weiterhin und gibt `"break"` zurueck.
- Grip-Bindings nutzen weiterhin denselben Start-, Drag- und End-Callback-Satz.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-drag-callback.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-drag-callback.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_drag_callback_binds_drag_context`
- `test_standalone_radio_pane_drag_callback_propagates_drag_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `170 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `172 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2408 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_drag_callback_helper`: best of 5 `294 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-drag-callback`.
