# 13 Radio Detach Ack Step Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `0c6fe483`
- Operation: Detach-Ack-Schritt aus `radio_proc` und `attempts_left` bestimmen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- `SimpleNamespace` statt Tk-App
- Keine Tk-Timer gestartet
- Keine IPC-, Datei- oder Subprocess-Zugriffe gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_detach_ack_step_inline` | 0.03236726600152906 s |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_detach_ack_step_helper` | 0.06203502799871785 s |

## Bewertung

- Der neue Helper fuegt nur minimalen Funktionsaufruf-Overhead hinzu.
- Der Unterschied ist fuer Detach-Handover nicht relevant.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Detach-Handover-Laufzeit haengt eher von Prozessstart, IPC und Tk-Timern ab.

## Aussagekraft

- Die Messung prueft nur die ausgelagerte Step-Entscheidung.
- Reale Detach-Uebergabe haengt staerker von Prozess- und Playback-Zustand ab.
