# 13 Radio Tab Clear Host

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Clear-Host-Adapter fuer den Radio-Tab
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `build_radio_tab`, Wechsel zwischen eingebettetem Panel und Detached-Placeholder

## Abhaengigkeiten und Seiteneffekte

- Der Host wird weiterhin ueber `_clear_radio_host` geleert.
- Das aktuelle `radio_embedded_panel` wird weiterhin vor dem Leeren aus dem App-State gelesen.
- `app.radio_embedded_panel` wird weiterhin auf `None` gesetzt.
- Der Bottom-Placeholder wird weiterhin nach dem Leeren angezeigt.
- Detached- und Embedded-Wechsel bleiben unveraendert.

## Risiken

- Das eingebettete Panel muss weiterhin vor dem Zerstoeren gestoppt werden.
- Der App-State muss auch ohne vorhandenes Panel auf `None` gesetzt werden.
- Der Bottom-Placeholder muss weiterhin nach jedem Clear angezeigt werden.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `6563aa3e`
- Messbedingungen: Dummy-App, Dummy-Host, Dummy-Panel, Dummy-Child und Dummy-Placeholder, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_tab_clear_host`: best of 5 `263 ns`

## Geplante kleine Aenderung

- Radio-Tab-spezifischen Clear-Host-Ablauf in `_clear_radio_tab_host` extrahieren.
- Direkte Tests fuer Panel-Reset plus Placeholder und fehlendes Panel ergaenzen.
- Generischen Host-Clear-Helper unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_clear_radio_tab_host` eingefuehrt.
- `build_radio_tab` nutzt den Helper im lokalen Clear-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Eingebettete Radio-Panels werden weiterhin gestoppt.
- Host-Kinder werden weiterhin zerstoert.
- `radio_embedded_panel` wird weiterhin zurueckgesetzt.
- Der untere Placeholder erscheint weiterhin nach dem Clear.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-tab-clear-host.md`
- `docs/refactoring/performance/areas/13-radio-tab-clear-host.md`

## Hinzugefuegte Tests

- `test_clear_radio_tab_host_stops_panel_resets_state_and_shows_placeholder`
- `test_clear_radio_tab_host_handles_missing_panel_and_shows_placeholder`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `192 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `194 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2271 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_tab_clear_host`: best of 5 `278 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us im Dummy-Pfad.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Widgets statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keinen manuellen Wechsel zwischen Embedded und Detached.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-tab-clear-host`.
