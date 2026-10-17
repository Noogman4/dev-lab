# 13 Standalone Radio Marker Bind Callbacks

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Binding-Installation fuer Standalone-Radio-Pane-Marker-Callbacks aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Binding-Plan wird weiterhin ueber `_standalone_radio_pane_marker_binding_plan` erzeugt.
- Event-Binding erfolgt weiterhin ueber `_standalone_radio_pane_bind_marker_events`.
- Binding-Fehler werden weiterhin im bestehenden Bind-Helper geschluckt.
- Marker-Erzeugung, Drag-State und Initial-Update bleiben unveraendert.

## Risiken

- Die Reihenfolge der Binding-Installation muss erhalten bleiben.
- Container und Pane muessen weiterhin dieselben Update-Bindings bekommen.
- Grip muss weiterhin Start-, Motion- und End-Callbacks bekommen.
- Fehlerverhalten beim Binden darf sich nicht aendern.

## Performance Vorher

- Commit vorher: `25dff393`
- Messbedingungen: direkter Plan-Loop mit Dummy-Plan und Dummy-Binder, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_bind_callbacks_inline`: best of 5 `232 ns`

## Geplante kleine Aenderung

- Binding-Installation in `_standalone_radio_pane_bind_marker_callbacks` extrahieren.
- Direkte Tests fuer vollstaendige Binding-Reihenfolge und Binder-Fehler ergaenzen.
- Binding-Spezifikationen und lokale Callback-Signaturen unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_bind_marker_callbacks` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer den bestehenden Binding-Plan.
- Tests fuer Plan-Reihenfolge und Fehlerdurchreichung des injizierten Binders ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Container und Pane erhalten weiterhin Configure, ButtonRelease und B1-Motion als Update-Bindings.
- Grip erhaelt weiterhin Button-1, B1-Motion und ButtonRelease als Drag-Bindings.
- Bind-Fehler verlassen weiterhin nicht den Tk-Installationspfad.
- Initiales Marker-Update bleibt unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-bind-callbacks.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-bind-callbacks.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_bind_marker_callbacks_binds_plan_in_order`
- `test_standalone_radio_pane_bind_marker_callbacks_propagates_binder_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `152 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `154 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2390 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_bind_callbacks_helper`: best of 5 `258 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-bind-callbacks`.
