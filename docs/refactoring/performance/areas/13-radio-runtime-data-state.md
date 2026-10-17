# 13 Radio Runtime Data State Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `54ba16a1`
- Operation: Radio-Daten- und Auswahl-State auf einem `SimpleNamespace` initialisieren
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Pfad ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_runtime_data_state_inline` | 0.49489559100038605 s |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_runtime_data_state_helper` | 0.6810308980002446 s |

## Bewertung

- Die neuen Helper fuegen nur kleinen Aufruf- und Test-Lambda-Overhead hinzu.
- Die Operation laeuft einmal beim App-Start und ist nicht laufzeitkritisch.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Wichtiger fuer Startzeit sind Tk-Initialisierung und Runtime-Ladevorgaenge.

## Aussagekraft

- Die Messung prueft nur Attributzuweisungen mit Dummy-Settings.
- Reale Startzeit haengt staerker von GUI- und Runtime-Ladevorgaengen ab.
