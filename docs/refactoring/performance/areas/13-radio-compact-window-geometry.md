# 13 Radio Compact Window Geometry Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `06ffd402`
- Operation: kompakte Standalone-Fenstergeometrie aus Request- und Screen-Werten berechnen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Keine Tk-Fenster gestartet
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_compact_window_geometry_inline` | 0.6599256030003744 s |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_compact_window_geometry_helper` | 0.7069952000001649 s |

## Bewertung

- Der neue Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Unterschied ist fuer den einmaligen Standalone-Fensterstart nicht relevant.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Fensterstart haengt eher von Tk, Theme-Anwendung und Widget-Aufbau ab.

## Aussagekraft

- Die Messung prueft nur die ausgelagerte Integer-Rechnung.
- Reale Startzeit haengt staerker von Tk und dem gesamten UI-Aufbau ab.
