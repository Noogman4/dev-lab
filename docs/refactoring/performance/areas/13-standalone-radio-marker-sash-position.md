# 13 Standalone Radio Marker Sash Position Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `0c4109eb`
- Operation: Sash-Position fuer Standalone-Radio-Pane-Marker mit Dummy-Pane setzen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Pfad ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `standalone_radio_sash_pos_inline` | 49 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `standalone_radio_sash_pos_helper` | 66 ns |

## Bewertung

- Der extrahierte Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter ist echte Tk-Pane- und Drag-Event-Arbeit.

## Aussagekraft

- Die Messung prueft nur den Dummy-Pfad der Sash-Positionierung.
- Reale Laufzeit haengt staerker von Tk ab.
