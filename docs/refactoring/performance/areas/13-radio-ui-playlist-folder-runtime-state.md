# 13 Radio UI Playlist Folder Runtime State Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `87fb63ab`
- Operation: Playlist-/Folder-Runtime-State auf einem `SimpleNamespace` initialisieren
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Pfad ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_ui_playlist_folder_runtime_state_inline` | 1.502659236000909 s |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_ui_playlist_folder_runtime_state_helper` | 1.6732723400000395 s |

## Bewertung

- Die neuen Helper fuegen nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation laeuft einmal beim UI-Start und ist nicht laufzeitkritisch.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Wichtiger fuer Startzeit sind Tk-Variablen- und Widget-Erzeugung.

## Aussagekraft

- Die Messung prueft nur Playlist- und Folder-Runtime-Attributzuweisungen.
- Reale Startzeit haengt staerker von Tk-Initialisierung und Widget-Aufbau ab.
