# 13 Radio Marker Drag End Callback Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `22996977`
- Operation: Marker-Drag-End-Callback fuer den Update-Callback erzeugen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Update-Callback und Dummy-Handler ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_drag_end_callback` | 61 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_drag_end_callback` | 122 ns |

## Bewertung

- Der extrahierte Helper fuegt nur den erwartbaren Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echtes Marker-Update nach Drag-End.

## Aussagekraft

- Die Messung prueft nur die Callback-Erzeugung.
- Reale Laufzeit haengt staerker vom Update-Callback, Sash-Lesen und Marker-Platzieren ab.
