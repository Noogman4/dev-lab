# 13 Radio Marker Single Bind

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: einzelner Tk-Event-Bind des Pane-Drag-Markers
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_bind_radio_pane_marker_events`

## Abhaengigkeiten und Seiteneffekte

- Batch-Binding erfolgt weiterhin ueber `_bind_radio_pane_marker_events`.
- Fehlerbehandlung bleibt weiterhin im Batch-Helper.
- Einzelne Bindings nutzen weiterhin `add="+"`.
- Binding-Plan, Callback-Aktivierung und Drag-Verhalten bleiben unveraendert.

## Risiken

- Einzel-Bind muss weiterhin exakt `widget.bind(event_name, callback, add="+")` ausfuehren.
- Batch-Helper muss weiterhin beim ersten Binding-Fehler abbrechen und den Fehler schlucken.
- Bestehende Binding-Reihenfolge darf sich nicht aendern.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `4ce6caf2`
- Messbedingungen: Dummy-Widget und Dummy-Callback, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_single_bind`: best of 5 `49 ns`

## Geplante kleine Aenderung

- Einzelnes `widget.bind(..., add="+")` in `_bind_radio_pane_marker_event` extrahieren.
- Direkten Test fuer den Einzel-Bind ergaenzen.
- Batch-Helper auf den neuen Einzel-Bind-Helper umstellen.

## Durchgefuehrte Aenderungen

- `_bind_radio_pane_marker_event` eingefuehrt.
- `_bind_radio_pane_marker_events` nutzt den neuen Helper pro Binding.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Alle Marker-Bindings werden weiterhin mit `add="+"` registriert.
- Batch-Binding stoppt weiterhin beim ersten Fehler.
- Binding-Fehler werden weiterhin geschluckt.
- Radio-Tab-Aufbau bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-single-bind.md`
- `docs/refactoring/performance/areas/13-radio-marker-single-bind.md`

## Hinzugefuegte Tests

- `test_bind_radio_pane_marker_event_binds_with_add`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `244 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `245 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2322 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_single_bind`: best of 5 `80 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-single-bind`.
