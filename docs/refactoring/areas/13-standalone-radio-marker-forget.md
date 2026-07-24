# 13 Standalone Radio Marker Forget

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Verstecken des Standalone-Radio-Pane-Markers aus den Fallback-Zweigen herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- `_install_pane_drag_marker` behandelt Placement- und Update-Fehler weiterhin selbst.
- `_standalone_radio_pane_forget_marker` ruft nur `marker.place_forget()` auf.
- Die Fehler werden weiterhin an den bisherigen Stellen ignoriert.
- Keine Callback- oder Binding-Logik wird veraendert.

## Risiken

- `place_forget` muss weiterhin in beiden Fallback-Zweigen aufgerufen werden.
- Fehler aus `place_forget` muessen weiterhin ignoriert werden.
- Echte Tk-Widgets duerfen nicht ersetzt werden.
- Standalone-UI-Source-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `b60754b0`
- Messbedingungen: direkter `place_forget()`-Aufruf mit Dummy-Marker, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_forget_inline`: best of 5 `19 ns`

## Geplante kleine Aenderung

- Marker-Verstecken in `_standalone_radio_pane_forget_marker` extrahieren.
- Direkten Test fuer `place_forget` ergaenzen.
- `_install_pane_drag_marker` an beiden Fallback-Stellen auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_forget_marker` eingefuehrt.
- `_install_pane_drag_marker` nutzt den neuen Helper in Placement- und Update-Fallbacks.
- Neuer Test `test_standalone_radio_pane_forget_marker_forgets_place` ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker wird weiterhin per `place_forget()` versteckt.
- Fehler beim Verstecken werden weiterhin ignoriert.
- Platzierungs- und Update-Fallbacks bleiben erhalten.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-forget.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-forget.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_forget_marker_forgets_place`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `124 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `125 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2361 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_forget_helper`: best of 5 `37 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen das Verstecken mit Dummy-Marker, nicht echte Standalone-Marker-Drag-Bedienung.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-forget`.
