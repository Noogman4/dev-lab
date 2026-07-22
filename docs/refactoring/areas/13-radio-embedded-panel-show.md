# 13 Radio Embedded Panel Show

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Anzeigeablauf fuer das eingebettete Radio-Panel
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `build_radio_tab`, Refresh-Entscheidung fuer Embedded-Modus

## Abhaengigkeiten und Seiteneffekte

- Bereits aktiver Embedded-Modus wird weiterhin uebersprungen.
- Der Radio-Host wird weiterhin vor dem Panel-Aufbau geleert.
- Detach-Callback ruft weiterhin `_detach_radio_from_tab(app)` auf.
- Panel-Aufbau verwendet weiterhin `NetMonRadioPanel(host, on_detach=..., host_app=app)`.
- Panel-State wird weiterhin ueber `_attach_embedded_radio_panel` gesetzt.

## Risiken

- Der Skip bei `radio_launcher_mode == "embedded"` muss erhalten bleiben.
- Der Detach-Callback muss weiterhin an dieselbe App gebunden sein.
- Source-basierte Radio-Tests erwarten weiterhin eine `NetMonRadioPanel`-Referenz in `build_radio_tab`.
- Der Helper darf keine neue Widget-Struktur einfuehren.

## Performance Vorher

- Commit vorher: `f3aef195`
- Messbedingungen: Dummy-App, Dummy-Host, Dummy-Clear und Dummy-Panel, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_embedded_panel_show`: best of 5 `682 ns`

## Geplante kleine Aenderung

- Embedded-Panel-Anzeige in `_show_radio_embedded_panel` extrahieren.
- Direkte Tests fuer Skip und kompletten Aufbau mit Detach-Callback ergaenzen.
- Lokalen `_show_embedded_panel`-Callback und Source-Hinweis erhalten.

## Durchgefuehrte Aenderungen

- `_show_radio_embedded_panel` eingefuehrt.
- `build_radio_tab` nutzt den Helper im lokalen Embedded-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Embedded-Modus baut weiterhin ein `NetMonRadioPanel`.
- Bereits embedded bleibt weiterhin ohne erneuten Aufbau.
- Host-Clear laeuft weiterhin vor dem Panel-Aufbau.
- Detach aus dem Panel startet weiterhin die externe Radio-App.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-embedded-panel-show.md`
- `docs/refactoring/performance/areas/13-radio-embedded-panel-show.md`

## Hinzugefuegte Tests

- `test_show_radio_embedded_panel_skips_when_already_embedded`
- `test_show_radio_embedded_panel_clears_builds_attaches_and_detaches`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `196 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `198 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2275 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_embedded_panel_show`: best of 5 `772 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt im Dummy-Pfad unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Panel statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keinen manuellen Embedded-/Detach-Wechsel.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-embedded-panel-show`.
