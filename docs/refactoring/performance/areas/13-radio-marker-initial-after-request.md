# 13 Radio Marker Initial After Request Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `ae77921d`
- Operation: Dummy-Callback per Dummy-Container-`after(0, ...)` anfordern
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Container und Dummy-Callback ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_initial_after_request` | 39 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_initial_after_request` | 63 ns |

## Bewertung

- Der extrahierte Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter sind echte Tk-`after`-Callbacks und Marker-Platzierung.

## Aussagekraft

- Die Messung prueft nur den Dummy-Pfad des initialen `after(0)`-Requests.
- Reale Laufzeit haengt staerker vom Tk-Eventloop ab.
