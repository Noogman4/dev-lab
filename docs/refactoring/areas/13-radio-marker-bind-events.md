# 13 Radio Marker Bind Events

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: fehlertolerantes Binden von Radio-Pane-Marker-Events
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Container-/Pane-Update-Bindings und Grip-Drag-Bindings

## Abhaengigkeiten und Seiteneffekte

- `widget.bind(..., add="+")` bleibt fuer alle Marker-Event-Bindings erhalten.
- Fehler beim Binden werden weiterhin geschluckt.
- Wenn ein Bind-Aufruf innerhalb eines Widget-Blocks fehlschlaegt, werden die restlichen Bindings dieses Blocks weiterhin nicht versucht.
- Marker-Geometrie, Sash-Positionierung, Drag-State und Update-Scheduling bleiben unveraendert.
- Keine Aenderung an Radio-Start, Detach/Reattach oder Embedded-Panel.

## Risiken

- Die Event-Namen und Callback-Zuordnung muessen unveraendert bleiben.
- Das bisherige Abbruchverhalten bei einem Bind-Fehler muss erhalten bleiben.
- Der Helper darf keine Tk-Widgets erzeugen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `b6bfa80a`
- Messbedingungen: Dummy-Widget mit `bind`, drei Event-Bindings, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_bind_events`: best of 5 `197 ns`

## Geplante kleine Aenderung

- Wiederholte `bind(..., add="+")`-Try/Except-Bloecke in `_bind_radio_pane_marker_events` extrahieren.
- Direkte Tests fuer erfolgreiche Bindings und Fehler-Abbruch ergaenzen.
- Marker-Drag-Logik, Update-Scheduling und Pane-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_bind_radio_pane_marker_events` eingefuehrt.
- Container-/Pane-Bindings und Grip-Bindings nutzen den Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Container und Pane erhalten weiterhin Configure-, ButtonRelease- und Motion-Bindings.
- Grip erhaelt weiterhin Button-, Motion- und ButtonRelease-Bindings.
- Alle Bindings nutzen weiterhin `add="+"`.
- Bind-Fehler bleiben toleriert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-bind-events.md`
- `docs/refactoring/performance/areas/13-radio-marker-bind-events.md`

## Hinzugefuegte Tests

- `test_bind_radio_pane_marker_events_binds_all_events_with_add`
- `test_bind_radio_pane_marker_events_stops_and_ignores_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `155 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `157 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --quiet netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: wegen Black-Timeout abgebrochen

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2234 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_bind_events`: best of 5 `212 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Widgets statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-bind-events`.
