# 13 Standalone Radio Marker Binding Plan Targets Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `d1d7946a`
- Operation: Standalone-Radio-Pane-Marker-Binding-Plan bauen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Pfad ohne echte Tk-Widgets oder Tk-Events
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse

| Operation | Best of 5 |
| --- | ---: |
| `standalone_radio_marker_binding_plan_current` | 102 ns |
| `standalone_radio_marker_binding_plan_targets` | 172 ns |

## Bewertung

- Die zwei zusaetzlichen Zielplan-Helper zeigen nur kleinen Funktionsaufruf-Overhead.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter ist echte Tk-Binding-Arbeit.

## Aussagekraft

- Die Messung prueft nur den erfolgreichen Dummy-Pfad.
- Reale Laufzeit haengt staerker von Tk-Event-Binding ab.
