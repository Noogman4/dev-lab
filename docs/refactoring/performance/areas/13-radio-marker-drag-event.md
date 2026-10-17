# 13 Radio Marker Drag Event Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `7efe63be`
- Operation: Drag-Motion ausfuehren und Tk-Callback mit `"break"` beenden
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Event, Dummy-Pane, Dict-State und Dummy-Callbacks ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_drag_event` | 294 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_drag_event` | 327 ns |

## Bewertung

- Der extrahierte Helper fuegt keine relevante Laufzeit hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Widget-, Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echte Tk-Event-Verarbeitung und Marker-Platzierung.

## Aussagekraft

- Die Messung prueft nur den erfolgreichen Dummy-Pfad.
- Reale Laufzeit haengt staerker von Tk-Event-Verarbeitung und Display-Verarbeitung ab.
