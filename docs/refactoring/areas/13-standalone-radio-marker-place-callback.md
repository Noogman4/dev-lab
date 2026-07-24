# 13 Standalone Radio Marker Place Callback

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: gebundenen Marker-Place-Callback fuer den Standalone-Radio-Pane-Marker aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Marker-Platzierung laeuft weiterhin ueber `_standalone_radio_pane_place_marker_for_sash_safe`.
- Der neue Helper bindet nur Container, Marker und `y_offset`.
- Drag-Motion ruft weiterhin einen einfachen `place_marker_for_sash(sash_y)`-Callback auf.
- Fehler beim eigentlichen Drag-Event werden weiterhin in `_standalone_radio_pane_drag_event` toleriert.

## Risiken

- Callback muss Container, Marker, Sash-Wert und Offset unveraendert weiterreichen.
- Fehler des injizierten Place-Helpers duerfen im Callback nicht versehentlich geschluckt werden.
- Der Legacy-Source-Hinweis fuer `marker_width = min(66, max(width - 24, 42))` muss im Installer sichtbar bleiben.
- Drag-Rechnung, Safe-Forget-Verhalten und Scheduling duerfen unveraendert bleiben.

## Performance Vorher

- Commit vorher: `d3e16f85`
- Messbedingungen: Dummy-Container, Dummy-Marker, Dummy-Place-Helper, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_place_callback_inline`: best of 5 `231 ns`

## Geplante kleine Aenderung

- Lokalen `_place_marker_for_sash`-Wrapper in `_standalone_radio_pane_place_callback` extrahieren.
- Direkte Tests fuer gebundene Marker-Kontextargumente und Fehlerpropagation ergaenzen.
- Restlichen Marker-Installer unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_place_callback` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer den Marker-Place-Callback.
- Tests fuer gebundene Argumente und Fehlerpropagation ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker-Geometry wird weiterhin ueber `_standalone_radio_pane_marker_geometry` gebaut.
- Marker-Place nutzt weiterhin `marker.place(**geometry)` und `marker.lift()`.
- Safe-Place vergisst den Marker weiterhin bei Place-Fehlern.
- Drag-Motion setzt, platziert und scheduled weiterhin in derselben Reihenfolge.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-place-callback.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-place-callback.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_place_callback_binds_marker_context`
- `test_standalone_radio_pane_place_callback_propagates_place_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `162 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `164 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2400 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_place_callback_helper`: best of 5 `263 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-place-callback`.
