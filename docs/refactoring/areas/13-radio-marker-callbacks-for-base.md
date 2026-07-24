# 13 Radio Marker Callbacks For Base

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Callback-Aufbau aus `_RadioPaneMarkerBase`
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_build_radio_pane_marker_installation`

## Abhaengigkeiten und Seiteneffekte

- `_build_radio_pane_marker_installation` baut weiterhin zuerst die Base und danach die Callbacks.
- `_build_radio_pane_marker_callbacks_for_base` reicht nur `base.marker` und `base.drag_state` an den Callback-Builder weiter.
- `base.grip` bleibt unveraendert fuer die spaetere Installation erhalten.
- Die Callback-Erstellung selbst bleibt unveraendert.

## Risiken

- `base.marker` und `base.drag_state` muessen exakt unveraendert an den Callback-Builder gehen.
- `base.grip` darf beim Callback-Aufbau nicht versehentlich verwendet oder ersetzt werden.
- Fehler aus dem Callback-Builder duerfen nicht geschluckt werden.
- Die Reihenfolge Base-Aufbau vor Callback-Aufbau muss erhalten bleiben.

## Performance Vorher

- Commit vorher: `0bddcf0f`
- Messbedingungen: direkter Callback-Builder-Aufruf mit Dummy-Objekten, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_callbacks_for_base_inline`: best of 5 `64 ns`

## Geplante kleine Aenderung

- Callback-Aufbau aus einer `_RadioPaneMarkerBase` in `_build_radio_pane_marker_callbacks_for_base` extrahieren.
- Direkten Test fuer die Feldweitergabe ergaenzen.
- `_build_radio_pane_marker_installation` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_build_radio_pane_marker_callbacks_for_base` eingefuehrt.
- `_build_radio_pane_marker_installation` nutzt den neuen Helper fuer den Callback-Aufbau.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Der Callback-Builder erhaelt weiterhin `container`, `pane`, `base.marker` und `base.drag_state`.
- Rueckgabe ist weiterhin die vom Callback-Builder erzeugte `_RadioPaneMarkerCallbacks`-Instanz.
- Die Installation nutzt weiterhin `base.marker`, `base.grip` und die Callback-Felder.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-callbacks-for-base.md`
- `docs/refactoring/performance/areas/13-radio-marker-callbacks-for-base.md`

## Hinzugefuegte Tests

- `test_build_radio_pane_marker_callbacks_for_base_passes_base_fields`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `276 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `277 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2354 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_callbacks_for_base_helper`: best of 5 `82 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets und Callback-Funktionen.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-callbacks-for-base`.
