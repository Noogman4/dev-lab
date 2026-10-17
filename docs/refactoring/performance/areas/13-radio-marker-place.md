# 13 Radio Marker Place Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `28257fb9`
- Operation: `marker.place(**geometry)` plus `marker.lift()` mit Dummy-Marker
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Marker ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_place` | 272 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_place` | 295 ns |

## Bewertung

- Der extrahierte Helper fuegt keine relevante Laufzeit hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Widget-, Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echte Tk-Marker-Platzierung und Rendering.

## Aussagekraft

- Die Messung prueft nur den erfolgreichen Dummy-Pfad.
- Reale Laufzeit haengt staerker von Tk-Event-Verarbeitung und Marker-Platzierung ab.
