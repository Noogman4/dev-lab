# 13 Radio Drag State Init

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Initialisierung des Drag-State fuer den Radio-Pane-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Marker-Drag-Start und Marker-Drag-Bewegung

## Abhaengigkeiten und Seiteneffekte

- `root_y` startet weiterhin mit `0`.
- `sash_y` startet weiterhin mit `0`.
- `update_pending` startet weiterhin mit `False`.
- Jeder Marker-Installer-Aufruf bekommt weiterhin einen eigenen Dict-Zustand.
- Marker-Geometrie, Sash-Positionierung, Drag-Handler und Bindings bleiben unveraendert.

## Risiken

- Der Helper darf keinen geteilten Mutable-State zurueckgeben.
- Die bestehenden Dict-Keys muessen unveraendert bleiben.
- Der Helper darf keine Tk-Widgets erzeugen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `7e02bcb7`
- Messbedingungen: direkter Dict-Literal-Aufbau, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_drag_state_init`: best of 5 `55 ns`

## Geplante kleine Aenderung

- Drag-State-Dict in `_radio_pane_drag_state` extrahieren.
- Direkten Test fuer Defaults und getrennte Dict-Instanzen ergaenzen.
- Marker-Drag-Logik, Update-Scheduling und Pane-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_radio_pane_drag_state` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer den initialen Drag-State.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Drag-Start schreibt weiterhin `root_y` und `sash_y`.
- Drag-Update nutzt weiterhin `update_pending`.
- Jeder Marker hat weiterhin seinen eigenen Drag-State.
- Drag-Handler geben weiterhin `"break"` zurueck.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-drag-state-init.md`
- `docs/refactoring/performance/areas/13-radio-drag-state-init.md`

## Hinzugefuegte Tests

- `test_radio_pane_drag_state_returns_defaults_and_new_dict`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `154 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `155 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --quiet netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: wegen Black-Timeout abgebrochen

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2232 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_drag_state_init`: best of 5 `67 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen den Dict-Zustand ohne echte Tk-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Drag-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-drag-state-init`.
