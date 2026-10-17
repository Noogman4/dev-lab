# 13 Radio Bottom Placeholder

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Aufbau des unteren Radio-Tab-Placeholders
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: Radio-Tab-Aufbau, Host-Clear, Detach/Reattach-Refresh

## Abhaengigkeiten und Seiteneffekte

- Zerstoert weiterhin vorhandene Kinder im unteren Radio-Bereich.
- Erstellt weiterhin ein linksbuendiges Hinweis-Label mit `wraplength=900`.
- Grid-Position bleibt `row=0`, `column=0`, `sticky="nw"`.
- Sichtbarer Text wird weiterhin im App-Kontext per `app.tr` bestimmt.
- Keine Aenderung an Radio-Start, Detach/Reattach oder Embedded-Panel.

## Risiken

- Vorhandene Placeholder-Kinder muessen beim Neuaufbau entfernt werden.
- Fehler beim Zerstoeren alter Widgets duerfen den Refresh weiterhin nicht abbrechen.
- Uebersetzungslogik darf nicht in den Helper wandern.
- Source-basierte Radio-Tests duerfen nicht durch Layout-Umbau gebrochen werden.

## Performance Vorher

- Commit vorher: `4e6ba0c5`
- Messbedingungen: synthetischer Container mit zwei Dummy-Kindern und Dummy-Label, direkter Destroy-/Label-/Grid-Ablauf, `time.perf_counter()`, 1000 Wiederholungen.
- `radio_bottom_placeholder`: Median `0.0005 ms`

## Geplante kleine Aenderung

- Direkte Tests fuer den Bottom-Placeholder-Aufbau ergaenzen.
- Destroy-/Label-/Grid-Ablauf aus der verschachtelten `_show_bottom_placeholder`-Funktion in einen internen Helper extrahieren.
- Textauswahl, Layoutwerte und Radio-Kommandos unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_show_radio_bottom_placeholder` eingefuehrt.
- `_show_bottom_placeholder` bestimmt weiterhin den uebersetzten Text und delegiert den Widget-Aufbau an den Helper.
- Fehlerbehandlung beim Zerstoeren alter Kinder bleibt unveraendert tolerant.
- Keine sichtbaren Texte, Layoutwerte oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Vorhandene Kinder im unteren Radio-Bereich werden vor dem Placeholder-Neuaufbau zerstoert.
- Das Placeholder-Label nutzt weiterhin `justify="left"` und `wraplength=900`.
- Das Label wird weiterhin an `row=0`, `column=0`, `sticky="nw"` positioniert.
- Fehler beim Entfernen alter Kinder brechen den Refresh nicht ab.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-bottom-placeholder.md`
- `docs/refactoring/performance/areas/13-radio-bottom-placeholder.md`

## Hinzugefuegte Tests

- `test_show_radio_bottom_placeholder_replaces_children_with_label`
- `test_show_radio_bottom_placeholder_ignores_destroy_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `128 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `130 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/ui/tabs/radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2207 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_bottom_placeholder`: Median `0.0005 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 ms.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Container und Dummy-Label statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Radio-Tab-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-bottom-placeholder`.
