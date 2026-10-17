# 13 Radio Marker Callbacks Container

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Zusammenfassen der Marker-Callbacks in `_RadioPaneMarkerCallbacks`
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_build_radio_pane_marker_callbacks`

## Abhaengigkeiten und Seiteneffekte

- `_build_radio_pane_marker_callbacks` baut weiterhin alle Marker-Callbacks in derselben Reihenfolge.
- `_radio_pane_marker_callbacks` erstellt nur `_RadioPaneMarkerCallbacks(update_marker, start_drag, drag, end_drag)`.
- Die Rueckgabeform bleibt unveraendert.
- Callback-Build- und Aktivierungslogik bleiben unveraendert.

## Risiken

- Die Feldreihenfolge in `_RadioPaneMarkerCallbacks` muss exakt unveraendert bleiben.
- Gebaute Callback-Objekte duerfen nicht ersetzt oder neu sortiert werden.
- Fehler duerfen nicht geschluckt werden.
- Echte Tk-Callbacks duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `48dd1597`
- Messbedingungen: direkter `_RadioPaneMarkerCallbacks`-Aufbau mit Dummy-Callbacks, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_callbacks_container`: best of 5 `160 ns`

## Geplante kleine Aenderung

- Callback-Container-Aufbau in `_radio_pane_marker_callbacks` extrahieren.
- Direkten Test fuer Feldzuordnung ergaenzen.
- `_build_radio_pane_marker_callbacks` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_radio_pane_marker_callbacks` eingefuehrt.
- `_build_radio_pane_marker_callbacks` nutzt den neuen Helper fuer die Rueckgabe.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Rueckgabe ist weiterhin `_RadioPaneMarkerCallbacks`.
- Felder bleiben `update_marker`, `start_drag`, `drag`, `end_drag`.
- Alle Callback-Objekte bleiben dieselben Instanzen.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-callbacks-container.md`
- `docs/refactoring/performance/areas/13-radio-marker-callbacks-container.md`

## Hinzugefuegte Tests

- `test_radio_pane_marker_callbacks_groups_activation_callbacks`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `273 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `274 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2351 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_callbacks_container`: best of 5 `188 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Callback-Objekte statt echter Tk-Callbacks.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-callbacks-container`.
