# 13 Radio Marker Drag Start Callback Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `97983731`
- Operation: Marker-Drag-Start-Callback fuer `drag_state` und `pane` erzeugen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Drag-State, Dummy-Pane und Dummy-Handler ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_drag_start_callback` | 61 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_drag_start_callback` | 140 ns |

## Bewertung

- Der extrahierte Helper fuegt nur den erwartbaren Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echtes Event-Handling und Sash-Lesen.

## Aussagekraft

- Die Messung prueft nur die Callback-Erzeugung.
- Reale Laufzeit haengt staerker von Event-Daten, `sashpos` und Tk-Event-Verarbeitung ab.
