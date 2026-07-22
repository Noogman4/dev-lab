# 13 Radio Bottom Placeholder For App

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: App-basierter Adapter fuer den unteren Radio-Placeholder
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `build_radio_tab`, initialer Aufbau und Host-Clear-Pfad

## Abhaengigkeiten und Seiteneffekte

- Der Placeholder-Text wird weiterhin ueber `_radio_bottom_placeholder_text(app)` ermittelt.
- Das Ersetzen der Kinder laeuft weiterhin ueber `_show_radio_bottom_placeholder`.
- Fehler beim Zerstoeren alter Kinder werden weiterhin ignoriert.
- Layout, Pane-Gewichte und Radio-Host-Verhalten bleiben unveraendert.

## Risiken

- Der uebersetzte App-Text muss weiterhin an den Placeholder uebergeben werden.
- Bestehende Kinder muessen weiterhin vor dem neuen Label entfernt werden.
- Der Helper darf keine neue Widget-Struktur einfuehren.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `6fe7d374`
- Messbedingungen: Dummy-App, Dummy-Container, Dummy-Child und Dummy-Label, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_bottom_placeholder_for_app`: best of 5 `608 ns`

## Geplante kleine Aenderung

- App-basierten Placeholder-Adapter in `_show_radio_bottom_placeholder_for_app` extrahieren.
- Direkte Tests fuer uebersetzten Text und Ersetzen vorhandener Kinder ergaenzen.
- Bestehenden generischen Placeholder-Helper unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_show_radio_bottom_placeholder_for_app` eingefuehrt.
- `build_radio_tab` nutzt den Helper im lokalen Bottom-Placeholder-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Der untere Radio-Bereich zeigt weiterhin den bisherigen Placeholder-Text.
- Vorhandene Kinder im unteren Bereich werden weiterhin entfernt.
- Das neue Label nutzt weiterhin `justify="left"` und `wraplength=900`.
- Initialer Aufbau und Clear-Host-Pfad zeigen weiterhin den Placeholder.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-bottom-placeholder-for-app.md`
- `docs/refactoring/performance/areas/13-radio-bottom-placeholder-for-app.md`

## Hinzugefuegte Tests

- `test_show_radio_bottom_placeholder_for_app_uses_translated_text`
- `test_show_radio_bottom_placeholder_for_app_replaces_existing_children`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `190 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `192 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2269 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_bottom_placeholder_for_app`: best of 5 `639 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt im Dummy-Pfad unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Widgets statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Placeholder-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-bottom-placeholder-for-app`.
