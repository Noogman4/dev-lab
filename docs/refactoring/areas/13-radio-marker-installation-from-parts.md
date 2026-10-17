# 13 Radio Marker Installation From Parts

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Installation aus Marker-Base und Marker-Callbacks zusammensetzen
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_build_radio_pane_marker_installation`

## Abhaengigkeiten und Seiteneffekte

- `_build_radio_pane_marker_installation` baut weiterhin zuerst die Base und danach die Callbacks.
- `_radio_pane_marker_installation_from_parts` liest nur Felder aus `base` und `callbacks`.
- `_radio_pane_marker_installation` bleibt der zentrale Container-Helper.
- Widget-Build-, Callback-Build- und Aktivierungslogik bleiben unveraendert.

## Risiken

- `base.marker` und `base.grip` muessen exakt unveraendert in die Installation gehen.
- Callback-Felder muessen exakt unveraendert in die Installation gehen.
- `base.drag_state` darf nicht versehentlich in die Installation uebernommen werden.
- Die Reihenfolge Base-Aufbau vor Callback-Aufbau vor Installation muss erhalten bleiben.

## Performance Vorher

- Commit vorher: `b0999fd2`
- Messbedingungen: direkter Installationsaufbau aus Base- und Callback-Dummy-Objekten, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_installation_from_parts_inline`: best of 5 `284 ns`

## Geplante kleine Aenderung

- Installationsaufbau aus `base` und `callbacks` in `_radio_pane_marker_installation_from_parts` extrahieren.
- Direkten Test fuer Feldzuordnung ergaenzen.
- `_build_radio_pane_marker_installation` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_radio_pane_marker_installation_from_parts` eingefuehrt.
- `_build_radio_pane_marker_installation` nutzt den neuen Helper fuer die Rueckgabe.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Rueckgabe ist weiterhin `_RadioPaneMarkerInstallation`.
- Felder bleiben `marker`, `grip`, `update_marker`, `start_drag`, `drag`, `end_drag`.
- Alle Base- und Callback-Objekte bleiben dieselben Instanzen.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-installation-from-parts.md`
- `docs/refactoring/performance/areas/13-radio-marker-installation-from-parts.md`

## Hinzugefuegte Tests

- `test_radio_pane_marker_installation_from_parts_groups_fields`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `277 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `278 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2355 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_installation_from_parts_helper`: best of 5 `300 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets und Callback-Funktionen.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-installation-from-parts`.
