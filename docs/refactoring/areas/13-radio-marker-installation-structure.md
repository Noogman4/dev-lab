# 13 Radio Marker Installation Structure

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Rueckgabestruktur der Pane-Drag-Marker-Installation
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- `_build_radio_pane_marker_installation` erzeugt weiterhin Marker, Grip und Aktivierungs-Callbacks.
- `_install_pane_drag_marker` aktiviert weiterhin ueber `_activate_radio_pane_marker_callbacks`.
- Source-basierter Marker-Kommentar bleibt in `_install_pane_drag_marker` erhalten.
- Widget-Erzeugung, Callback-Erzeugung und Drag-Verhalten bleiben unveraendert.

## Risiken

- Die benannten Felder muessen exakt den bisherigen Tuple-Positionen entsprechen.
- Der Installer muss weiterhin Marker, Grip und alle Callbacks korrekt weiterreichen.
- Der Installer muss weiterhin den Marker zurueckgeben.
- Source-basierte Radio-Tests duerfen durch die interne Struktur nicht brechen.

## Performance Vorher

- Commit vorher: `67bf231c`
- Messbedingungen: Dummy-Container, Dummy-Pane, Dummy-Basis-Builder und Dummy-Callback-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_installation`: best of 5 `183 ns`

## Geplante kleine Aenderung

- 6er-Tuple-Rueckgabe durch `_RadioPaneMarkerInstallation` ersetzen.
- Installer auf Attributzugriff umstellen.
- Tests fuer Typ und Feldzuordnung ergaenzen.

## Durchgefuehrte Aenderungen

- `_RadioPaneMarkerInstallation` als `NamedTuple` eingefuehrt.
- `_build_radio_pane_marker_installation` gibt diese benannte Struktur zurueck.
- `_install_pane_drag_marker` nutzt benannte Felder statt Tuple-Entpackung.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker-Basis und Callback-Build laufen weiterhin in derselben Reihenfolge.
- Aktivierung erhaelt weiterhin Container, Pane, Grip und alle Callbacks.
- Marker-Install gibt weiterhin den Marker zurueck.
- Radio-Tab-Aufbau bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-installation-structure.md`
- `docs/refactoring/performance/areas/13-radio-marker-installation-structure.md`

## Angepasste Tests

- `test_build_radio_pane_marker_installation_builds_base_then_callbacks`
- `test_install_pane_drag_marker_activates_callbacks_without_direct_reschedule`

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

- `radio_marker_installation`: best of 5 `364 ns`

## Bewertung

- Die benannte Struktur kostet gegenueber dem rohen Tuple messbaren, aber sehr kleinen Overhead.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen, weil Lesbarkeit und Feldsicherheit hier wichtiger sind.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-installation-structure`.
