# 13 Standalone Radio Marker Bind Callback

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: einzelne Binding-Operation aus der Standalone-Radio-Pane-Marker-Binding-Plan-Iteration herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_bind_marker_callbacks`

## Abhaengigkeiten und Seiteneffekte

- Event-Binding bleibt bei `_standalone_radio_pane_bind_marker_events`.
- Binding-Plan-Iteration bleibt bei `_standalone_radio_pane_bind_marker_callbacks`.
- Aktives Callback-Binding bleibt bei `_standalone_radio_pane_bind_active_marker_callbacks`.
- Widget-Bau, Drag-Logik und sichtbares Marker-Verhalten bleiben unveraendert.

## Risiken

- Jedes Widget muss weiterhin mit seinem Binding-Set gebunden werden.
- Die Binding-Reihenfolge des Plans darf sich nicht aendern.
- Fehler aus dem einzelnen Bind-Aufruf duerfen weiterhin propagiert werden.
- Fehlerverhalten im tieferen Event-Bind-Helper bleibt unveraendert.

## Performance Vorher

- Commit vorher: `3f4351a3`
- Messbedingungen: zwei Dummy-Plan-Eintraege, Dummy-Binder, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_bind_callbacks_current`: best of 5 `137 ns`

## Geplante kleine Aenderung

- Einzelnen Bind-Aufruf in `_standalone_radio_pane_bind_marker_callback` extrahieren.
- Direkte Tests fuer Bind-Delegation und Fehlerpropagation ergaenzen.
- Plan-Iteration auf den neuen Einzel-Bind-Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_bind_marker_callback` eingefuehrt.
- `_standalone_radio_pane_bind_marker_callbacks` nutzt den neuen Helper pro Plan-Eintrag.
- Tests fuer Einzel-Bind, Fehlerfall und Plan-Reihenfolge ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Der Binding-Plan wird weiterhin in Reihenfolge iteriert.
- Jeder Plan-Eintrag wird weiterhin ueber den Event-Bind-Helper gebunden.
- Fehler aus der Plan-Iteration werden weiterhin propagiert.
- Aktives Callback-Binding nutzt weiterhin denselben Plan-Binder.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-bind-callback.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-bind-callback.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_bind_marker_callback_delegates_binding`
- `test_standalone_radio_pane_bind_marker_callback_propagates_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `244 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `246 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2482 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_bind_callbacks_single_helper`: best of 5 `185 ns`

## Bewertung

- Die einzelne Bind-Operation ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Binder statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-bind-callback`.
