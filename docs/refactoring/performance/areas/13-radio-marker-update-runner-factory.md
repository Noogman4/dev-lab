# 13 Radio Marker Update Runner Factory Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `d58eea3a`
- Operation: Runner fuer geplantes Marker-Update aus Dummy-Dependencies erzeugen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Drag-State, Dummy-Update-Callback und Dummy-Runner ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_update_runner_factory` | 59 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_update_runner_factory` | 177 ns |

## Bewertung

- Die extrahierte Factory erzeugt eine Closure und fuegt kleinen Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter sind echte Tk-Idle-Callbacks und Marker-Platzierung.

## Aussagekraft

- Die Messung prueft nur den Dummy-Pfad der Runner-Erzeugung.
- Reale Laufzeit haengt staerker vom Tk-Eventloop und vom Marker-Placement ab.
