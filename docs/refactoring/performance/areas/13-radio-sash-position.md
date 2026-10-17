# 13 Radio Sash Position Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `40df75a4`
- Operation: erfolgreiche Sash-Positionierung ueber `pane.sashpos(0, int(new_y))`
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Pane ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_sash_position` | 64 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_sash_position` | 82 ns |

## Bewertung

- Der extrahierte Helper fuegt keine relevante Laufzeit hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Widget-, Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echter Tk-Pane-Aufbau, Event-Verarbeitung und Rendering.

## Aussagekraft

- Die Messung prueft nur den erfolgreichen `sashpos`-Pfad mit Dummy-Objekt.
- Reale Laufzeit haengt staerker von Tk-Rendering, Pane-Events und Marker-Platzierung ab.
