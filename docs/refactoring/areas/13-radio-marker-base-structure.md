# 13 Radio Marker Base Structure

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Rueckgabestruktur der Pane-Drag-Marker-Basis
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_build_radio_pane_marker_installation`

## Abhaengigkeiten und Seiteneffekte

- `_build_radio_pane_marker_base` erzeugt weiterhin Marker, Grip und Drag-State.
- `_build_radio_pane_marker_installation` nutzt weiterhin Marker und Drag-State fuer den Callback-Build.
- Widget-Erzeugung, Callback-Erzeugung und Drag-Verhalten bleiben unveraendert.
- Source-basierter Marker-Kommentar bleibt in `_install_pane_drag_marker` erhalten.

## Risiken

- Die benannten Felder muessen exakt den bisherigen Tuple-Positionen entsprechen.
- Die Installation muss weiterhin Marker, Grip und Drag-State korrekt uebernehmen.
- Tests mit injizierten Basis-Buildern muessen dieselbe Struktur verwenden.
- Source-basierte Radio-Tests duerfen durch die interne Struktur nicht brechen.

## Performance Vorher

- Commit vorher: `13a963cd`
- Messbedingungen: Dummy-Container, Dummy-Widget-Builder und Dummy-Drag-State-Factory, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_base`: best of 5 `142 ns`

## Geplante kleine Aenderung

- 3er-Tuple-Rueckgabe durch `_RadioPaneMarkerBase` ersetzen.
- Installation auf Attributzugriff umstellen.
- Tests fuer Typ und Feldzuordnung anpassen.

## Durchgefuehrte Aenderungen

- `_RadioPaneMarkerBase` als `NamedTuple` eingefuehrt.
- `_build_radio_pane_marker_base` gibt diese benannte Struktur zurueck.
- `_build_radio_pane_marker_installation` nutzt benannte Basisfelder.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker und Grip werden weiterhin vor dem Drag-State erzeugt.
- Farbargument wird weiterhin an den Widget-Builder durchgereicht.
- Installation erhaelt weiterhin Marker, Grip und Drag-State.
- Marker-Install aktiviert weiterhin dieselben Callbacks und gibt den Marker zurueck.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-base-structure.md`
- `docs/refactoring/performance/areas/13-radio-marker-base-structure.md`

## Angepasste Tests

- `test_build_radio_pane_marker_base_builds_widgets_then_drag_state`
- `test_build_radio_pane_marker_installation_builds_base_then_callbacks`
- `test_build_radio_pane_marker_installation_uses_default_color_for_base`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `242 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `242 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2319 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_base`: best of 5 `295 ns`

## Bewertung

- `NamedTuple` erzeugt mehr Overhead als ein rohes Tuple.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen, weil die Feldnamen Positionsfehler vermeiden.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-base-structure`.
