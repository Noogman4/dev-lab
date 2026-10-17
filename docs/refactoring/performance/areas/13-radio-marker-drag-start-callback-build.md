# 13 Radio Marker Drag Start Callback Build Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `c5e7c2df`
- Operation: Dummy-Drag-Start-Callback-Factory mit Drag-State und Pane aufrufen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Factory ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_drag_start_callback_build` | 21 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_drag_start_callback_build` | 40 ns |

## Bewertung

- Der extrahierte Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter ist echte Tk-Widget-, Callback- und Drag-Event-Arbeit.

## Aussagekraft

- Die Messung prueft nur den Dummy-Pfad des Drag-Start-Callback-Aufbaus.
- Reale Laufzeit haengt staerker von Tk ab.
