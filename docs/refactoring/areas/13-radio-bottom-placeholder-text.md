# 13 Radio Bottom Placeholder Text

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Textauswahl fuer den unteren Radio-Placeholder
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: Radio-Tab-Aufbau, Host-Clear, Bottom-Placeholder-Aufbau

## Abhaengigkeiten und Seiteneffekte

- Nutzt weiterhin direkt `app.tr` fuer den Placeholder-Hinweis.
- Fallback-Text bleibt unveraendert.
- Fehlerverhalten von `app.tr` bleibt unveraendert, weil der Helper keine zusaetzliche Fehlerbehandlung einfuehrt.
- Widget-Aufbau und Grid-Werte bleiben unveraendert.
- Keine Aenderung an Radio-Start, Detach/Reattach oder Embedded-Panel.

## Risiken

- Der Uebersetzungsschluessel darf sich nicht aendern.
- Der Fallback-Text darf sich nicht aendern.
- Der Helper darf keine Tk-Widgets erzeugen.
- Source-basierte Radio-Tests duerfen nicht durch den Helper-Schnitt brechen.

## Performance Vorher

- Commit vorher: `899ad0f6`
- Messbedingungen: direkter `app.tr`-Aufruf mit Dummy-App, `time.perf_counter()`, 1000 Wiederholungen.
- `radio_bottom_placeholder_text`: Median `0.0001 ms`

## Geplante kleine Aenderung

- Direkten Test fuer die Bottom-Placeholder-Textauswahl ergaenzen.
- Inline-Textauswahl aus `_show_bottom_placeholder` in einen internen Helper extrahieren.
- Widget-Aufbau, Layoutwerte und Radio-Kommandos unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_radio_bottom_placeholder_text` eingefuehrt.
- `_show_bottom_placeholder` nutzt den Helper fuer den Hinweistext.
- Keine Widget-Struktur, Layoutwerte oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Uebersetzungsschluessel bleibt `radio_bottom_media_hint`.
- Fallback bleibt `This lower area is reserved for playlists and files.`
- Der Placeholder wird weiterhin durch `_show_radio_bottom_placeholder` aufgebaut.
- `app.tr`-Fehler wuerden weiterhin wie bisher durchgereicht.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-bottom-placeholder-text.md`
- `docs/refactoring/performance/areas/13-radio-bottom-placeholder-text.md`

## Hinzugefuegte Tests

- `test_radio_bottom_placeholder_text_uses_app_translation`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `137 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `138 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/ui/tabs/radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2215 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_bottom_placeholder_text`: Median `0.0001 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 ms.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen die Textauswahl direkt, aber keine vollstaendige manuelle Radio-Tab-Bedienung.
- Der GUI-Smoke prueft Startbarkeit, aber keine Detailinteraktion im unteren Radio-Bereich.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-bottom-placeholder-text`.
