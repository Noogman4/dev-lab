# 13 Radio Runtime Widget Refs Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `9d7fb38d`
- Operation: Widget-Referenzen auf einem `SimpleNamespace` initialisieren
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Pfad ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_runtime_widget_refs_inline` | 0.6986332180003956 s |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_runtime_widget_refs_helper` | 0.736213780000071 s |

## Bewertung

- Der neue Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation laeuft einmal beim App-Start und ist nicht laufzeitkritisch.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Wichtiger fuer Startzeit sind Pfad-, Tk- und Runtime-Ladevorgaenge.

## Aussagekraft

- Die Messung prueft nur Attributzuweisungen auf einem `SimpleNamespace`.
- Reale Startzeit haengt staerker von Tk-Initialisierung und Runtime-Ladevorgaengen ab.
