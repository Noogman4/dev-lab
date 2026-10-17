# 13 Standalone Radio Marker Initial Update

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: initialen `after(0)`-Update-Request fuer den Standalone-Radio-Pane-Marker aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Initiales Marker-Update wird weiterhin mit `container.after(0, update_marker)` geplant.
- Fehler beim `after`-Aufruf werden weiterhin ignoriert.
- Binding-Installation, Drag-Callbacks und Marker-Update-Logik bleiben unveraendert.
- Es wird kein sofortiger Fallback-Aufruf von `update_marker` eingefuehrt.

## Risiken

- Der Delay-Wert muss weiterhin exakt `0` bleiben.
- Der Callback muss unveraendert an `container.after` weitergereicht werden.
- Fehler beim `after`-Aufruf duerfen weiterhin nicht nach aussen laufen.
- Der Installer muss weiterhin den Marker zurueckgeben.

## Performance Vorher

- Commit vorher: `59f9e404`
- Messbedingungen: direkter `after(0, update_marker)`-Pfad mit Dummy-Container, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_initial_update_inline`: best of 5 `67 ns`

## Geplante kleine Aenderung

- Initialen `after(0)`-Request in `_standalone_radio_pane_request_initial_marker_update` extrahieren.
- Direkte Tests fuer erfolgreichen `after(0)`-Aufruf und Fehler-Toleranz ergaenzen.
- `_install_pane_drag_marker` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_request_initial_marker_update` eingefuehrt.
- `_install_pane_drag_marker` delegiert den initialen Update-Request an den neuen Helper.
- Tests fuer `after(0)` und ignorierten `after`-Fehler ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur, Binding- oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Initiales Marker-Update wird weiterhin nach Tk-Start mit `after(0, update_marker)` geplant.
- Fehler beim initialen Request werden weiterhin ignoriert.
- Der Marker wird weiterhin am Ende des Installers zurueckgegeben.
- Drag- und Binding-Verhalten bleibt unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-initial-update.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-initial-update.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_request_initial_marker_update_uses_after_zero`
- `test_standalone_radio_pane_request_initial_marker_update_ignores_after_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `154 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `156 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2392 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_initial_update_helper`: best of 5 `87 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Container statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-initial-update`.
