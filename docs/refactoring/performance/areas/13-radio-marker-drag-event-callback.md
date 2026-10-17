# 13 Radio Marker Drag Event Callback Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `bfd5cffc`
- Operation: Marker-Drag-Event-Callback fuer Drag-State, Pane, Platzierung und Scheduling erzeugen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Drag-State, Dummy-Pane, Dummy-Callbacks und Dummy-Handler ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_drag_event_callback` | 63 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_drag_event_callback` | 174 ns |

## Bewertung

- Der extrahierte Helper fuegt nur den erwartbaren Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echte Drag-Motion-Verarbeitung.

## Aussagekraft

- Die Messung prueft nur die Callback-Erzeugung.
- Reale Laufzeit haengt staerker von Event-Daten, Sash-Positionierung, Marker-Platzierung und Scheduling ab.
