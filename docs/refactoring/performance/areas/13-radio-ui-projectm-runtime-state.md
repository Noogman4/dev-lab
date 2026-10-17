# 13 Radio UI projectM Runtime State Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `3a3ec5db`
- Operation: projectM-Runtime-State auf einem `SimpleNamespace` initialisieren
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Pfad ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_ui_projectm_runtime_state_inline` | 0.2650483870002063 s |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_ui_projectm_runtime_state_helper` | 0.2788309060006213 s |

## Bewertung

- Der neue Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation laeuft einmal beim UI-Start und ist nicht laufzeitkritisch.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Wichtiger fuer Startzeit sind Tk-Variablen- und Widget-Erzeugung.

## Aussagekraft

- Die Messung prueft nur projectM-Runtime-Attributzuweisungen.
- Reale Startzeit haengt staerker von Tk-Initialisierung und Widget-Aufbau ab.
