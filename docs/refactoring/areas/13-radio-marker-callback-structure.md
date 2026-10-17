# 13 Radio Marker Callback Structure

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Rueckgabestruktur der Pane-Drag-Marker-Callbacks
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_build_radio_pane_marker_installation`

## Abhaengigkeiten und Seiteneffekte

- `_build_radio_pane_marker_callbacks` erzeugt weiterhin Update-, Start-, Drag- und End-Callback.
- `_build_radio_pane_marker_installation` nutzt weiterhin die erzeugten Callbacks fuer die Installation.
- Callback-Erzeugung laeuft weiterhin in derselben Reihenfolge.
- Widget-Erzeugung, Event-Bindings und Drag-Verhalten bleiben unveraendert.

## Risiken

- Die benannten Felder muessen exakt den bisherigen Tuple-Positionen entsprechen.
- Die Installation muss weiterhin alle Callback-Felder korrekt uebernehmen.
- Tests mit injizierten Callback-Buildern muessen dieselbe Struktur verwenden.
- Source-basierte Radio-Tests duerfen durch die interne Struktur nicht brechen.

## Performance Vorher

- Commit vorher: `8f460020`
- Messbedingungen: Dummy-Container, Dummy-Pane, Dummy-Marker, Dummy-Drag-State und Dummy-Callback-Factories, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_callbacks`: best of 5 `238 ns`

## Geplante kleine Aenderung

- 4er-Tuple-Rueckgabe durch `_RadioPaneMarkerCallbacks` ersetzen.
- Installation auf Attributzugriff umstellen.
- Tests fuer Typ und Feldzuordnung anpassen.

## Durchgefuehrte Aenderungen

- `_RadioPaneMarkerCallbacks` als `NamedTuple` eingefuehrt.
- `_build_radio_pane_marker_callbacks` gibt diese benannte Struktur zurueck.
- `_build_radio_pane_marker_installation` nutzt benannte Callback-Felder.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Place-, Update-, Schedule-, Start-, Drag- und End-Callbacks entstehen weiterhin in gleicher Reihenfolge.
- Installation erhaelt weiterhin Update-, Start-, Drag- und End-Callback.
- Marker-Install aktiviert weiterhin dieselben Callbacks.
- Radio-Tab-Aufbau bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-callback-structure.md`
- `docs/refactoring/performance/areas/13-radio-marker-callback-structure.md`

## Angepasste Tests

- `test_build_radio_pane_marker_callbacks_builds_callbacks_in_dependency_order`
- `test_build_radio_pane_marker_callbacks_returns_activation_callbacks`
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

- `radio_marker_callbacks`: best of 5 `394 ns`

## Bewertung

- `NamedTuple` erzeugt mehr Overhead als ein rohes Tuple.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen, weil die Feldnamen Positionsfehler vermeiden.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-callback-structure`.
