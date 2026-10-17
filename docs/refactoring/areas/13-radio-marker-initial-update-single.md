# 13 Radio Marker Initial Update Single

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: initiales Marker-Update nach Callback-Aktivierung
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Callback-Aktivierung erfolgt weiterhin ueber `_activate_radio_pane_marker_callbacks`.
- Initiales Marker-Update wird weiterhin innerhalb der Aktivierung geplant.
- Direkter zweiter Schedule-Aufruf im Installer entfaellt.
- Marker-Callback-Erzeugung bleibt unveraendert.
- Source-basierter Marker-Kommentar bleibt unveraendert.

## Risiken

- Initiales Marker-Update darf nicht versehentlich entfallen.
- Es darf nicht doppelt geplant werden.
- Installer muss weiterhin den Marker zurueckgeben.
- Source-basierte Radio-Tests duerfen durch die Korrektur nicht brechen.

## Verhalten Vorher

- Commit vorher: `57714596`
- Dummy-Installer-Pruefung: `activate,direct_schedule`
- Das initiale Update wurde nach der Aktivierung zusaetzlich direkt geplant.

## Geplante kleine Aenderung

- Direkten `_schedule_initial_radio_pane_marker_update`-Aufruf aus `_install_pane_drag_marker` entfernen.
- Installer-Test mit Dummies ergaenzen, der die Aktivierung und das Fehlen eines direkten Reschedule prueft.
- Callback-Factories unveraendert lassen.

## Durchgefuehrte Aenderungen

- Doppelten direkten Initial-Update-Schedule entfernt.
- `test_install_pane_drag_marker_activates_callbacks_without_direct_reschedule` ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker-Callbacks werden weiterhin aktiviert.
- Initiales Marker-Update wird weiterhin geplant.
- Marker wird weiterhin zurueckgegeben.
- Drag- und Update-Callbacks bleiben unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-initial-update-single.md`
- `docs/refactoring/performance/areas/13-radio-marker-initial-update-single.md`

## Hinzugefuegte Tests

- `test_install_pane_drag_marker_activates_callbacks_without_direct_reschedule`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `235 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `236 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2313 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Verhalten Nachher

- Dummy-Installer-Pruefung: `activate`
- Das initiale Update wird nur noch ueber die Aktivierung geplant.

## Bewertung

- Doppeltes Scheduling entfernt.
- Keine Performance-Optimierung vorgenommen; die Aenderung entfernt nur einen redundanten Aufruf.
- Der Installer bleibt kleiner und eindeutiger.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-initial-update-single`.
