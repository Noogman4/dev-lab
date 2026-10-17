# 13 Radio UI projectM Vars Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `2f5d4014`
- Operation: projectM-StringVars auf einem `SimpleNamespace` initialisieren
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Var-Builder ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine projectM-Subprozesse gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_ui_projectm_vars_inline` | 1.1708939939999254 s |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_ui_projectm_vars_helper` | 1.2696884100005263 s |

## Bewertung

- Der neue Helper liegt praktisch im gleichen Zeitbereich wie der Inline-Block.
- Der kleine Unterschied ist fuer den einmaligen UI-Start nicht relevant.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Wichtiger fuer projectM-Laufzeit bleiben Sidecar-Prozesse, Preset-Zugriffe und echte UI-Updates.

## Aussagekraft

- Die Messung prueft nur den ausgelagerten Variablenblock mit Dummy-Variablen.
- Reale Startzeit haengt staerker von Tk, Bildaufbau und weiteren UI-Initialisierungen ab.
