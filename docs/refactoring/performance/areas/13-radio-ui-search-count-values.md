# 13 Radio UI Search Count Values Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `3e8b32f0`
- Operation: Suchtext- und DB-Count-Werte normalisieren
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Pfad ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_ui_search_count_values_inline` | 0.07673324600000342 s |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_ui_search_count_values_helper` | 0.11710662099994806 s |

## Bewertung

- Die neuen Helper fuegen nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation laeuft einmal beim UI-Start und ist nicht laufzeitkritisch.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Wichtiger fuer Startzeit sind Tk-Variablen- und Widget-Erzeugung.

## Aussagekraft

- Die Messung prueft nur Settings- und Count-Normalisierung.
- Reale Startzeit haengt staerker von Tk-Initialisierung und Widget-Aufbau ab.
