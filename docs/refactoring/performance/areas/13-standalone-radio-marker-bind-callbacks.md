# 13 Standalone Radio Marker Bind Callbacks Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `25dff393`
- Operation: Binding-Plan fuer Standalone-Radio-Pane-Marker mit Dummy-Binder installieren
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Pfad ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `standalone_radio_marker_bind_callbacks_inline` | 232 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `standalone_radio_marker_bind_callbacks_helper` | 258 ns |

## Bewertung

- Der extrahierte Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter ist echte Tk-Binding-Arbeit.

## Aussagekraft

- Die Messung prueft nur den erfolgreichen Dummy-Pfad.
- Reale Laufzeit haengt staerker von Tk-Event-Binding ab.
