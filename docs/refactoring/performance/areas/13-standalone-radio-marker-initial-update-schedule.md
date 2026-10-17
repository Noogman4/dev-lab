# 13 Standalone Radio Marker Initial Update Schedule Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `f28a524c`
- Operation: initiales Update-Scheduling fuer Standalone-Radio-Pane-Marker an Request-Callback delegieren
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Pfad ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `standalone_radio_marker_initial_update_schedule_inline` | 66 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `standalone_radio_marker_initial_update_schedule_helper` | 94 ns |

## Bewertung

- Der extrahierte Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter ist echte Tk-`after`-Verarbeitung.

## Aussagekraft

- Die Messung prueft nur den erfolgreichen Dummy-Pfad.
- Reale Laufzeit haengt staerker von Tk-Event-Verarbeitung ab.
