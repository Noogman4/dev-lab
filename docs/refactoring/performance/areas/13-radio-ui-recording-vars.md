# 13 Radio UI Recording Vars Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `36cf4b03`
- Operation: Recording-StringVars auf einem `SimpleNamespace` initialisieren
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Var-Builder ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Datei- oder Aufnahmeprozesse gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_ui_recording_vars_inline` | 0.5318704139990587 s |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_ui_recording_vars_helper` | 0.5746121180000046 s |

## Bewertung

- Der neue Helper liegt praktisch im gleichen Zeitbereich wie der Inline-Block.
- Der kleine Unterschied ist fuer den einmaligen UI-Start nicht relevant.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Wichtiger fuer Recording-Laufzeit bleiben echte Datei-, ffmpeg- und UI-Update-Pfade.

## Aussagekraft

- Die Messung prueft nur den ausgelagerten Variablenblock mit Dummy-Variablen.
- Reale Startzeit haengt staerker von Tk, Bildaufbau und weiteren UI-Initialisierungen ab.
