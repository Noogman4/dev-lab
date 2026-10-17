# 13 Radio UI Volume EQ Search Vars Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `9052ffbe`
- Operation: Volume-, Equalizer- und Such-Variablen auf einem `SimpleNamespace` initialisieren
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Var-Builder ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_ui_volume_eq_search_vars_inline` | 1.9567533569988882 s |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_ui_volume_eq_search_vars_helper` | 1.9925489609995566 s |

## Bewertung

- Der neue Helper liegt praktisch im gleichen Zeitbereich wie der Inline-Block.
- Der kleine Unterschied ist fuer den einmaligen UI-Start nicht relevant.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Wichtiger fuer Startzeit bleiben echte Tk-Initialisierung und Widget-Aufbau.

## Aussagekraft

- Die Messung prueft nur den ausgelagerten Variablenblock mit Dummy-Variablen.
- Reale Startzeit haengt staerker von Tk, Bildaufbau und weiteren UI-Initialisierungen ab.
