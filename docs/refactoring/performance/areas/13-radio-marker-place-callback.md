# 13 Radio Marker Place Callback Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `4280f43a`
- Operation: Marker-Platzierungs-Callback fuer `container` und `marker` erzeugen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Container, Dummy-Marker und Dummy-Placer ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_place_callback` | 60 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_place_callback` | 138 ns |

## Bewertung

- Der extrahierte Helper fuegt nur den erwartbaren Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echte Tk-Marker-Platzierung.

## Aussagekraft

- Die Messung prueft nur die Callback-Erzeugung.
- Reale Laufzeit haengt staerker von Tk-Geometry, `place` und `lift` ab.
