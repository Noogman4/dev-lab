# 13 Standalone Radio Marker Callbacks Build

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Callback-Zusammenbau fuer den Standalone-Radio-Pane-Marker aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Drag-State wird weiterhin ueber `_standalone_radio_pane_drag_state` gebaut.
- Sash-, Place-, Update-, Schedule-, Start-, Drag- und End-Callbacks werden weiterhin ueber die bestehenden Helper gebaut.
- Binding-Aktivierung bleibt in `_standalone_radio_pane_activate_marker_bindings`.
- Der neue Helper gibt nur die vier Callbacks zurueck, die die Aktivierung braucht.

## Risiken

- Builder-Reihenfolge muss erhalten bleiben, weil spaetere Callbacks vorherige Ergebnisse verwenden.
- Update-, Start-, Drag- und End-Callbacks muessen unveraendert zurueckgegeben werden.
- Fehler der Builder duerfen nicht versehentlich geschluckt werden.
- Der Legacy-Source-Hinweis fuer `marker_width = min(66, max(width - 24, 42))` muss im Installer sichtbar bleiben.

## Performance Vorher

- Commit vorher: `c29f6ec5`
- Messbedingungen: Dummy-Container, Dummy-Pane, Dummy-Marker, Dummy-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_callbacks_build_inline`: best of 5 `352 ns`

## Geplante kleine Aenderung

- Callback-Zusammenbau in `_standalone_radio_pane_marker_callbacks` extrahieren.
- Direkte Tests fuer Builder-Reihenfolge, Rueckgabewerte und Fehlerpropagation ergaenzen.
- Widget-Erzeugung und Binding-Aktivierung unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_callbacks` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer den Callback-Zusammenbau.
- Tests fuer Builder-Reihenfolge, Rueckgabewerte und Fehlerpropagation ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Marker und Grip werden weiterhin zuerst erstellt.
- Die vier Aktivierungs-Callbacks bleiben Update, Start, Drag und End.
- Binding-Aktivierung erhaelt weiterhin Container, Pane, Grip und dieselben Callbacks.
- Der Installer gibt weiterhin den Marker zurueck.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-callbacks-build.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-callbacks-build.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_callbacks_builds_callbacks_in_order`
- `test_standalone_radio_pane_marker_callbacks_propagates_builder_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `178 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `180 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2416 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_callbacks_build_helper`: best of 5 `394 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-callbacks-build`.
