# 13 Radio Detach Ready Ack Payload Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `28b89dd3`
- Operation: Detach-Ready-Ack-Payload fuer Timeout-Fall erzeugen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Keine Tk-Fenster gestartet
- Keine IPC-, Datei- oder Subprocess-Zugriffe gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_detach_ready_ack_payload_inline` | 0.06889957999919716 s |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_detach_ready_ack_payload_helper` | 0.07753565399980289 s |

## Bewertung

- Der neue Helper fuegt nur minimalen Funktionsaufruf-Overhead hinzu.
- Der Unterschied ist fuer Detach-Handover nicht relevant.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Detach-Handover-Laufzeit haengt eher von Prozessstart, IPC und Tk-Timern ab.

## Aussagekraft

- Die Messung prueft nur die ausgelagerte Dict-Erzeugung.
- Reale Detach-Uebergabe haengt staerker von Prozess- und Playback-Zustand ab.
