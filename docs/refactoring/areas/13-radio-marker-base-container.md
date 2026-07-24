# 13 Radio Marker Base Container

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Zusammenfassen der Marker-Basis in `_RadioPaneMarkerBase`
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_build_radio_pane_marker_base`

## Abhaengigkeiten und Seiteneffekte

- `_build_radio_pane_marker_base` baut weiterhin zuerst Marker-Widgets und danach Drag-State.
- `_radio_pane_marker_base` erstellt nur `_RadioPaneMarkerBase(marker, grip, drag_state)`.
- Die Rueckgabeform bleibt unveraendert.
- Widget-Build-, Callback-Build- und Aktivierungslogik bleiben unveraendert.

## Risiken

- Die Feldreihenfolge in `_RadioPaneMarkerBase` muss exakt unveraendert bleiben.
- Marker-, Grip- und Drag-State-Objekte duerfen nicht ersetzt oder neu sortiert werden.
- Fehler duerfen nicht geschluckt werden.
- Echte Tk-Widgets und Drag-Callbacks duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `7779a731`
- Messbedingungen: direkter `_RadioPaneMarkerBase`-Aufbau mit Dummy-Objekten, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_base_container_inline`: best of 5 `155 ns`

## Geplante kleine Aenderung

- Base-Container-Aufbau in `_radio_pane_marker_base` extrahieren.
- Direkten Test fuer Feldzuordnung ergaenzen.
- `_build_radio_pane_marker_base` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_radio_pane_marker_base` eingefuehrt.
- `_build_radio_pane_marker_base` nutzt den neuen Helper fuer die Rueckgabe.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Rueckgabe ist weiterhin `_RadioPaneMarkerBase`.
- Felder bleiben `marker`, `grip`, `drag_state`.
- Alle Marker-, Grip- und Drag-State-Objekte bleiben dieselben Instanzen.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-base-container.md`
- `docs/refactoring/performance/areas/13-radio-marker-base-container.md`

## Hinzugefuegte Tests

- `test_radio_pane_marker_base_groups_widget_and_drag_state`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `275 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `276 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2353 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_base_container_helper`: best of 5 `181 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets und Drag-State-Instanzen.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-base-container`.
