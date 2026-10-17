# 13 Radio Marker Scheduled Update Run Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `25eaf41d`
- Operation: Pending-Flag zuruecksetzen und Dummy-Update-Callback ausfuehren
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Drag-State und Dummy-Update-Callback ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_scheduled_update_run` | 103 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_scheduled_update_run` | 70 ns |

## Bewertung

- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.
- Die Messabweichung im Dummy-Pfad ist fuer reale Tk-Updates nicht relevant.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter sind echte Tk-Idle-Callbacks und Marker-Platzierung.

## Aussagekraft

- Die Messung prueft nur den Dummy-Pfad des geplanten Update-Runs.
- Reale Laufzeit haengt staerker vom Tk-Eventloop und vom Marker-Placement ab.
