# 13 Standalone Radio Marker Binding Spec Helpers Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `d6598a85`
- Operation: Update- und Grip-Bindings bauen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Pfad ohne echte Tk-Widgets oder Tk-Events
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse

| Operation | Best of 5 |
| --- | ---: |
| `standalone_radio_marker_binding_builders_current` | 156 ns |
| `standalone_radio_marker_binding_builders_specs` | 676 ns |

## Bewertung

- Die Spec-Helper fuegen Python-Iterator- und Funktionsaufruf-Overhead hinzu.
- Die Dummy-Operation bleibt unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Falls dieser Pfad jemals relevant wuerde, koennten die Builder wieder direkte Tupel bauen.
- Aktuell ist echte Tk-Binding-Arbeit klar relevanter.

## Aussagekraft

- Die Messung prueft nur den erfolgreichen Dummy-Pfad.
- Reale Laufzeit haengt staerker von Tk-Event-Binding ab.
