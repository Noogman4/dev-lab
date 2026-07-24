# 13 Standalone Radio Marker Install Parts

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: verbleibende Installations-Orchestrierung fuer den Standalone-Radio-Pane-Marker aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Callback-Satz wird weiterhin ueber `_standalone_radio_pane_marker_callbacks` gebaut.
- Binding-Aktivierung laeuft weiterhin ueber `_standalone_radio_pane_activate_marker_bindings`.
- Der neue Helper gibt weiterhin den Marker zurueck.
- Widget-Erzeugung bleibt weiterhin in `_standalone_radio_pane_marker_widgets`.

## Risiken

- Callback-Build muss Container, Pane, Marker und Offset unveraendert erhalten.
- Binding-Aktivierung muss Container, Pane, Grip und alle vier Callbacks unveraendert erhalten.
- Rueckgabewert muss weiterhin der Marker sein.
- Der Legacy-Source-Hinweis fuer `marker_width = min(66, max(width - 24, 42))` muss im Installer sichtbar bleiben.

## Performance Vorher

- Commit vorher: `d2fb9fda`
- Messbedingungen: Dummy-Container, Dummy-Pane, Dummy-Marker, Dummy-Grip, Dummy-Callback-Builder, Dummy-Aktivierung, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_install_parts_inline`: best of 5 `202 ns`

## Geplante kleine Aenderung

- Callback-Build plus Binding-Aktivierung in `_standalone_radio_pane_install_marker_parts` extrahieren.
- Direkte Tests fuer Verdrahtung, Rueckgabewert und Fehlerpropagation ergaenzen.
- Widget-Erzeugung und sichtbares Marker-Verhalten unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_install_marker_parts` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper nach der Widget-Erzeugung.
- Tests fuer Callback-/Binding-Verdrahtung, Rueckgabewert und Fehlerpropagation ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Marker und Grip werden weiterhin zuerst erstellt.
- Callback-Build laeuft weiterhin vor Binding-Aktivierung.
- Binding-Aktivierung erhaelt weiterhin Update, Start, Drag und End.
- Der Installer gibt weiterhin den Marker zurueck.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-install-parts.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-install-parts.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_install_marker_parts_builds_callbacks_and_activates`
- `test_standalone_radio_pane_install_marker_parts_propagates_activation_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `180 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `182 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2418 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_install_parts_helper`: best of 5 `216 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-install-parts`.
