# 13 Radio Language Code Config Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `65820471`
- Operation: Sprachcode aus Config-Payload normalisieren
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dict-Payload ohne Datei-I/O
- Keine Tk-Fenster gestartet
- Keine Sprachdateien geladen
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_language_code_config_inline` | 0.08908957800122153 s |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_language_code_config_helper` | 0.12287723400004325 s |

## Bewertung

- Der neue Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Unterschied ist fuer den App-Start nicht relevant.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Sprachstartzeit haengt eher von Datei-I/O und JSON-Laden ab.

## Aussagekraft

- Die Messung prueft nur die ausgelagerte Payload-Normalisierung.
- Reale Startzeit haengt staerker von Datei-I/O, Tk und dem gesamten UI-Aufbau ab.
