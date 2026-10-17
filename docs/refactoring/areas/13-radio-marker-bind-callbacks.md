# 13 Radio Marker Bind Callbacks

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Binding-Installation fuer Radio-Pane-Marker-Callbacks
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Container-, Pane- und Grip-Bindings

## Abhaengigkeiten und Seiteneffekte

- Update-Bindings werden weiterhin auf Container und Pane installiert.
- Grip-Bindings werden weiterhin auf dem Grip-Widget installiert.
- Alle Bindings verwenden weiterhin `add="+"`.
- Fehler einzelner Widget-Bindings werden weiterhin in `_bind_radio_pane_marker_events` geschluckt.
- Marker-Erzeugung, Drag-State und Initial-Update bleiben unveraendert.

## Risiken

- Die Reihenfolge der Binding-Installation muss erhalten bleiben.
- Container und Pane muessen weiterhin dieselben Update-Bindings bekommen.
- Grip muss weiterhin Start-, Motion- und End-Callbacks bekommen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `99b024cb`
- Messbedingungen: Dummy-Widgets und Dummy-Callbacks, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_bind_callbacks`: best of 5 `786 ns`

## Geplante kleine Aenderung

- Binding-Installation in `_bind_radio_pane_marker_callbacks` extrahieren.
- Direkte Tests fuer vollstaendige Binding-Reihenfolge und Bind-Fehler ergaenzen.
- Binding-Spezifikationen und lokale Callback-Signaturen unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_bind_radio_pane_marker_callbacks` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer Container-, Pane- und Grip-Bindings.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Container und Pane erhalten weiterhin Configure, ButtonRelease und B1-Motion als Update-Bindings.
- Grip erhaelt weiterhin Button-1, B1-Motion und ButtonRelease als Drag-Bindings.
- Bind-Fehler verlassen weiterhin nicht den Tk-Installationspfad.
- Initiales Marker-Update bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-bind-callbacks.md`
- `docs/refactoring/performance/areas/13-radio-marker-bind-callbacks.md`

## Hinzugefuegte Tests

- `test_bind_radio_pane_marker_callbacks_binds_update_and_grip_events`
- `test_bind_radio_pane_marker_callbacks_ignores_widget_bind_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `184 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `186 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2263 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_bind_callbacks`: best of 5 `822 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt im Dummy-Pfad unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Widgets statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Drag-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-bind-callbacks`.
