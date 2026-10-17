# 13 Standalone Radio Marker Sash Callback

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: gebundenen Sash-Setter fuer den Standalone-Radio-Pane-Marker aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Sash-Position wird weiterhin ueber `_standalone_radio_pane_set_sash_pos` gesetzt.
- Drag-Motion ruft weiterhin einen einfachen `set_sash_pos(new_y)`-Callback auf.
- Fehler beim eigentlichen Drag-Event werden weiterhin in `_standalone_radio_pane_drag_event` toleriert.
- Der neue Helper bindet nur das Pane-Objekt an den bestehenden Setter.

## Risiken

- Der Callback muss exakt dasselbe Pane-Objekt weiterreichen.
- Fehler des Setters duerfen im Callback nicht versehentlich geschluckt werden.
- Drag-Rechnung, Marker-Platzierung und Scheduling duerfen unveraendert bleiben.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `0c24e10f`
- Messbedingungen: Dummy-Pane, Dummy-Setter, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_set_sash_callback_inline`: best of 5 `181 ns`

## Geplante kleine Aenderung

- Lokalen `_set_sash_pos`-Wrapper in `_standalone_radio_pane_sash_callback` extrahieren.
- Direkte Tests fuer Pane-Bindung und Fehlerpropagation ergaenzen.
- Restlichen Marker-Installer unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_sash_callback` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer den Drag-Sash-Setter.
- Tests fuer gebundenes Pane und Fehlerpropagation ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Sash-Setzen bevorzugt weiterhin `pane.sashpos(0, int(new_y))`.
- Fallback auf `pane.sash_place(0, 0, int(new_y))` bleibt unveraendert.
- Drag-Motion setzt, platziert und scheduled weiterhin in derselben Reihenfolge.
- Drag-Event gibt weiterhin `"break"` zurueck.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-sash-callback.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-sash-callback.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_sash_callback_binds_pane`
- `test_standalone_radio_pane_sash_callback_propagates_set_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `160 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `162 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2398 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_set_sash_callback_helper`: best of 5 `215 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Panes.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-sash-callback`.
