# 13 Radio UI Header Vars Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `b01b5db2`
- Operation: Header-, Status-, Stream- und Listen-StringVars auf einem `SimpleNamespace` initialisieren
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Var-Builder ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_ui_header_vars_inline` | 1.7028966560010304 s |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_ui_header_vars_helper` | 1.712749784999687 s |

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
