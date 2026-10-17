# 13 Standalone Radio Marker Bind Callback Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `3f4351a3`
- Operation: Standalone-Radio-Pane-Marker-Binding-Plan binden
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Zwei Dummy-Plan-Eintraege
- Dummy-Pfad ohne echte Tk-Widgets oder Tk-Events
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `standalone_radio_marker_bind_callbacks_current` | 137 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `standalone_radio_marker_bind_callbacks_single_helper` | 185 ns |

## Bewertung

- Die zusaetzliche Einzel-Bind-Ebene zeigt nur kleinen Funktionsaufruf-Overhead.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter ist echte Tk-Binding-Arbeit.

## Aussagekraft

- Die Messung prueft nur den erfolgreichen Dummy-Pfad.
- Reale Laufzeit haengt staerker von Tk-Event-Binding ab.
