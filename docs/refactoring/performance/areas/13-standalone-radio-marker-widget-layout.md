# 13 Standalone Radio Marker Widget Layout Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `4e6f3b53`
- Operation: Marker-Spalte konfigurieren und Grip-Label grid-setzen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Pfad ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `standalone_radio_marker_widget_layout_inline` | 273 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `standalone_radio_marker_widget_layout_helper` | 276 ns |

## Bewertung

- Der extrahierte Helper fuegt praktisch keinen relevanten Overhead hinzu.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter ist echte Tk-Widget- und Layout-Verarbeitung.

## Aussagekraft

- Die Messung prueft nur den erfolgreichen Dummy-Pfad.
- Reale Laufzeit haengt staerker von Tk-Widget-Erzeugung ab.
