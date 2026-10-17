# 13 Standalone Radio Marker Initial Update After Args Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `fb91c2b4`
- Operation: Standalone-Radio-Pane-Marker-Initial-Update per `after` anfordern
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Pfad ohne echte Tk-Widgets oder Tk-Events
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `standalone_radio_marker_initial_update_after_current` | 45 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `standalone_radio_marker_initial_update_after_args` | 88 ns |

## Bewertung

- Die zusaetzliche Argument-Helper-Ebene zeigt nur kleinen Funktionsaufruf-Overhead.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter ist echte Tk-Scheduling-Arbeit.

## Aussagekraft

- Die Messung prueft nur den erfolgreichen Dummy-Pfad.
- Reale Laufzeit haengt staerker von Tk-Event-Verarbeitung ab.
