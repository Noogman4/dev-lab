# 13 Radio Marker Update Callback Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `37e78719`
- Operation: Marker-Update-Callback fuer `pane`, Platzierungs-Callback und `marker` erzeugen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Pane, Dummy-Place-Callback, Dummy-Marker und Dummy-Handler ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_update_callback` | 72 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_update_callback` | 162 ns |

## Bewertung

- Der extrahierte Helper fuegt nur den erwartbaren Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echtes Tk-Sash-Lesen und Marker-Platzieren.

## Aussagekraft

- Die Messung prueft nur die Callback-Erzeugung.
- Reale Laufzeit haengt staerker von `sashpos`, Geometry, `place` und `lift` ab.
