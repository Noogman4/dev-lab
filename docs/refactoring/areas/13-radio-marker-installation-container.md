# 13 Radio Marker Installation Container

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Zusammenfassen der Marker-Installation in `_RadioPaneMarkerInstallation`
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_build_radio_pane_marker_installation`

## Abhaengigkeiten und Seiteneffekte

- `_build_radio_pane_marker_installation` baut weiterhin zuerst Base und danach Callbacks.
- `_radio_pane_marker_installation` erstellt nur `_RadioPaneMarkerInstallation(marker, grip, update_marker, start_drag, drag, end_drag)`.
- Die Rueckgabeform bleibt unveraendert.
- Callback-Build- und Aktivierungslogik bleiben unveraendert.

## Risiken

- Die Feldreihenfolge in `_RadioPaneMarkerInstallation` muss exakt unveraendert bleiben.
- Gebaute Marker-, Grip- und Callback-Objekte duerfen nicht ersetzt oder neu sortiert werden.
- Fehler duerfen nicht geschluckt werden.
- Echte Tk-Callbacks duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `37a52bb9`
- Messbedingungen: direkter `_RadioPaneMarkerInstallation`-Aufbau mit Dummy-Objekten, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_installation_container`: best of 5 `192 ns`

## Geplante kleine Aenderung

- Installation-Container-Aufbau in `_radio_pane_marker_installation` extrahieren.
- Direkten Test fuer Feldzuordnung ergaenzen.
- `_build_radio_pane_marker_installation` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_radio_pane_marker_installation` eingefuehrt.
- `_build_radio_pane_marker_installation` nutzt den neuen Helper fuer die Rueckgabe.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Rueckgabe ist weiterhin `_RadioPaneMarkerInstallation`.
- Felder bleiben `marker`, `grip`, `update_marker`, `start_drag`, `drag`, `end_drag`.
- Alle Marker- und Callback-Objekte bleiben dieselben Instanzen.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-installation-container.md`
- `docs/refactoring/performance/areas/13-radio-marker-installation-container.md`

## Hinzugefuegte Tests

- `test_radio_pane_marker_installation_groups_marker_dependencies`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `274 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `275 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2352 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_installation_container`: best of 5 `208 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets und Callbacks.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-installation-container`.
