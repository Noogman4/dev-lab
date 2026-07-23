# 13 Radio Marker Callbacks Build

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Erzeugung der Pane-Drag-Marker-Callbacks
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Platzierungs-, Update-, Schedule-, Start-, Drag- und End-Callback werden weiterhin in derselben Reihenfolge erzeugt.
- Callback-Abhaengigkeiten bleiben unveraendert.
- Installer aktiviert weiterhin nur die vier Callbacks fuer Binding und Initial-Update.
- Source-basierter Marker-Kommentar bleibt in `_install_pane_drag_marker` erhalten.
- Widget-Erzeugung und Drag-State-Erzeugung bleiben im Installer.

## Risiken

- Callback-Reihenfolge und Abhaengigkeiten muessen unveraendert bleiben.
- Der Installer muss weiterhin dieselben vier Aktivierungs-Callbacks erhalten.
- Kein Callback darf vorzeitig ausgefuehrt werden.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `96b8c303`
- Messbedingungen: Dummy-Objekte und Dummy-Callback-Factories, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_callbacks_build`: best of 5 `258 ns`

## Geplante kleine Aenderung

- Callback-Erzeugung in `_build_radio_pane_marker_callbacks` extrahieren.
- Direkte Tests fuer Reihenfolge und Rueckgabewerte ergaenzen.
- Installer-Test auf neue Abstraktionsgrenze anpassen.

## Durchgefuehrte Aenderungen

- `_build_radio_pane_marker_callbacks` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer die Callback-Erzeugung.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker-Callbacks werden weiterhin vollstaendig erzeugt.
- Callback-Aktivierung erhaelt weiterhin Update, Start, Drag und End.
- Marker-Install gibt weiterhin den Marker zurueck.
- Initiales Update bleibt weiterhin ueber die Aktivierung geplant.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-callbacks-build.md`
- `docs/refactoring/performance/areas/13-radio-marker-callbacks-build.md`

## Hinzugefuegte Tests

- `test_build_radio_pane_marker_callbacks_builds_callbacks_in_dependency_order`
- `test_build_radio_pane_marker_callbacks_returns_activation_callbacks`

## Angepasste Tests

- `test_install_pane_drag_marker_activates_callbacks_without_direct_reschedule`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `236 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `238 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2315 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_callbacks_build`: best of 5 `341 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-callbacks-build`.
