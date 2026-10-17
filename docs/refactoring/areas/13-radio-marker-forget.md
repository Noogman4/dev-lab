# 13 Radio Marker Forget

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: fehlertolerantes Ausblenden des Radio-Pane-Markers
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Marker-Platzierung und Marker-Update

## Abhaengigkeiten und Seiteneffekte

- `marker.place_forget()` wird weiterhin genutzt.
- Fehler beim Ausblenden werden weiterhin geschluckt.
- Marker-Geometrie, Sash-Positionierung, Drag-State und Bindings bleiben unveraendert.
- Keine Aenderung an Radio-Start, Detach/Reattach oder Embedded-Panel.

## Risiken

- Fehler beim Ausblenden duerfen weiterhin nicht nach aussen gelangen.
- Der Helper darf keine Tk-Widgets erzeugen.
- Beide bisherigen Fehlerpfade muessen weiterhin den Marker ausblenden versuchen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `4283bdb3`
- Messbedingungen: Dummy-Marker mit `place_forget`, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_forget`: best of 5 `27 ns`

## Geplante kleine Aenderung

- Wiederholten `place_forget`-Try/Except-Block in `_forget_radio_pane_marker` extrahieren.
- Direkte Tests fuer erfolgreichen Aufruf und Fehler-Toleranz ergaenzen.
- Marker-Platzierung, Drag-Handler und Pane-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_forget_radio_pane_marker` eingefuehrt.
- Zwei identische Fehlerpfade in `_install_pane_drag_marker` nutzen den Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Bei Marker-Platzierungsfehlern wird weiterhin `place_forget()` versucht.
- Bei Marker-Update-Fehlern wird weiterhin `place_forget()` versucht.
- Fehler beim Ausblenden bleiben toleriert.
- Drag-Handler geben weiterhin `"break"` zurueck.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-forget.md`
- `docs/refactoring/performance/areas/13-radio-marker-forget.md`

## Hinzugefuegte Tests

- `test_forget_radio_pane_marker_calls_place_forget`
- `test_forget_radio_pane_marker_ignores_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `152 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `154 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --quiet netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: wegen Black-Timeout abgebrochen

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2231 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_forget`: best of 5 `44 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Marker statt echter Tk-Frames.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-forget`.
