# 13 Radio Marker Base Build

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Basisaufbau des Pane-Drag-Markers
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Marker und Grip werden weiterhin ueber `_build_radio_pane_marker_widgets` erzeugt.
- Drag-State wird weiterhin ueber `_radio_pane_drag_state` erzeugt.
- Marker-Basisaufbau laeuft weiterhin vor Callback-Build und Aktivierung.
- Source-basierter Marker-Kommentar bleibt in `_install_pane_drag_marker` erhalten.
- Callback-Build und Aktivierung bleiben unveraendert.

## Risiken

- Marker, Grip und Drag-State muessen in derselben Reihenfolge entstehen.
- Farbargument muss weiterhin an den Widget-Builder durchgereicht werden.
- Installer muss weiterhin den Marker zurueckgeben.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `17ef18bc`
- Messbedingungen: Dummy-Container, Dummy-Widget-Builder und Dummy-Drag-State-Factory, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_base_build`: best of 5 `134 ns`

## Geplante kleine Aenderung

- Marker/Grip/Drag-State-Aufbau in `_build_radio_pane_marker_base` extrahieren.
- Direkte Tests fuer Reihenfolge, Rueckgabewerte und Farbdurchreichung ergaenzen.
- Installer-Test auf neue Abstraktionsgrenze anpassen.

## Durchgefuehrte Aenderungen

- `_build_radio_pane_marker_base` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer Marker, Grip und Drag-State.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker und Grip werden weiterhin mit der gewuenschten Farbe erzeugt.
- Drag-State wird weiterhin direkt nach dem Widget-Aufbau erzeugt.
- Callback-Build erhaelt weiterhin Marker und Drag-State.
- Marker-Install gibt weiterhin den Marker zurueck.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-base-build.md`
- `docs/refactoring/performance/areas/13-radio-marker-base-build.md`

## Hinzugefuegte Tests

- `test_build_radio_pane_marker_base_builds_widgets_then_drag_state`
- `test_build_radio_pane_marker_base_uses_default_color_for_widgets`

## Angepasste Tests

- `test_install_pane_drag_marker_activates_callbacks_without_direct_reschedule`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `238 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `240 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2317 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_base_build`: best of 5 `188 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-base-build`.
