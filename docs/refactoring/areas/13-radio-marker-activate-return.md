# 13 Radio Marker Activate Return

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Aktivieren einer Marker-Installation und Rueckgabe des Marker-Widgets
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- `_install_pane_drag_marker` baut weiterhin zuerst die Installation.
- `_activate_radio_pane_marker_and_return_marker` aktiviert die Installation und gibt danach `installation.marker` zurueck.
- `_activate_radio_pane_marker_installation` bleibt die zentrale Aktivierungsfunktion.
- Die Legacy-Source-Referenz in `_install_pane_drag_marker` bleibt erhalten.

## Risiken

- Die Aktivierung muss weiterhin vor der Rueckgabe des Markers laufen.
- `installation.marker` muss unveraendert zurueckgegeben werden.
- Monkeypatching von `_activate_radio_pane_marker_installation` muss fuer bestehende Tests moeglich bleiben.
- Fehler aus der Aktivierung duerfen nicht geschluckt werden.

## Performance Vorher

- Commit vorher: `c04a3780`
- Messbedingungen: direkter Aktivierungsaufruf mit Dummy-Objekten und Rueckgabe von `installation.marker`, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_activate_and_return_inline`: best of 5 `35 ns`

## Geplante kleine Aenderung

- Aktivieren und Marker-Rueckgabe in `_activate_radio_pane_marker_and_return_marker` extrahieren.
- Direkten Test fuer Aktivierungsreihenfolge und Rueckgabe ergaenzen.
- `_install_pane_drag_marker` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_activate_radio_pane_marker_and_return_marker` eingefuehrt.
- Der Helper loest die Standard-Aktivierungsfunktion zur Laufzeit auf, damit Monkeypatching stabil bleibt.
- `_install_pane_drag_marker` nutzt den neuen Helper fuer Aktivierung und Rueckgabe.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- `_install_pane_drag_marker` gibt weiterhin das Marker-Widget zurueck.
- Die Installation wird weiterhin aktiviert, bevor der Marker zurueckgegeben wird.
- Direkte initiale Scheduling-Aufrufe bleiben weiterhin vermieden.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-activate-return.md`
- `docs/refactoring/performance/areas/13-radio-marker-activate-return.md`

## Hinzugefuegte Tests

- `test_activate_radio_pane_marker_and_return_marker_activates_then_returns_marker`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `278 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `279 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2356 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_activate_and_return_helper`: best of 5 `67 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-activate-return`.
