# 13 Radio Marker Bind Events Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `b6bfa80a`
- Operation: drei fehlertolerante `widget.bind(..., add="+")`-Aufrufe mit Dummy-Widget
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Widget ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_bind_events` | 197 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_bind_events` | 212 ns |

## Bewertung

- Der extrahierte Helper fuegt keine relevante Laufzeit hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Widget-, Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echte Tk-Event-Verarbeitung und Rendering.

## Aussagekraft

- Die Messung prueft nur erfolgreiche Bind-Aufrufe mit Dummy-Objekt.
- Reale Laufzeit haengt staerker von Tk-Widget- und Event-Verarbeitung ab.
