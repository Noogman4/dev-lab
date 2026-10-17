# 13 Radio Marker Installation Build

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Zusammensetzen der Pane-Drag-Marker-Installation
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Marker, Grip und Drag-State werden weiterhin ueber `_build_radio_pane_marker_base` erzeugt.
- Aktivierungs-Callbacks werden weiterhin ueber `_build_radio_pane_marker_callbacks` erzeugt.
- Aktivierung und initiales Scheduling bleiben in `_activate_radio_pane_marker_callbacks`.
- Source-basierter Marker-Kommentar bleibt in `_install_pane_drag_marker` erhalten.
- Sichtbare Widget-Struktur und Drag-Verhalten bleiben unveraendert.

## Risiken

- Der Builder muss Marker und Grip unveraendert an den Installer zurueckgeben.
- Callback-Build muss weiterhin Marker und Drag-State aus der Basis erhalten.
- Farbargument muss weiterhin an den Basis-Builder durchgereicht werden.
- Installer muss weiterhin den Marker zurueckgeben.

## Performance Vorher

- Commit vorher: `ee46fc8e`
- Messbedingungen: Dummy-Container, Dummy-Pane, Dummy-Basis-Builder und Dummy-Callback-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_install_build`: best of 5 `136 ns`

## Geplante kleine Aenderung

- Basis- und Callback-Zusammenbau in `_build_radio_pane_marker_installation` extrahieren.
- Direkte Tests fuer Reihenfolge, Rueckgabewerte und Farbdurchreichung ergaenzen.
- Installer-Test auf neue Abstraktionsgrenze anpassen.

## Durchgefuehrte Aenderungen

- `_build_radio_pane_marker_installation` eingefuehrt.
- `_install_pane_drag_marker` nutzt den neuen Helper und aktiviert danach unveraendert.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker-Basis wird weiterhin vor Callback-Build erzeugt.
- Callback-Build erhaelt weiterhin Container, Pane, Marker und Drag-State.
- Marker-Aktivierung bindet weiterhin Container, Pane und Grip.
- Marker-Install gibt weiterhin den Marker zurueck.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-installation-build.md`
- `docs/refactoring/performance/areas/13-radio-marker-installation-build.md`

## Hinzugefuegte Tests

- `test_build_radio_pane_marker_installation_builds_base_then_callbacks`
- `test_build_radio_pane_marker_installation_uses_default_color_for_base`

## Angepasste Tests

- `test_install_pane_drag_marker_activates_callbacks_without_direct_reschedule`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `240 passed` vor Refactoring
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

- `radio_marker_install_build`: best of 5 `180 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-installation-build`.
