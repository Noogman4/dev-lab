# 13 Radio Marker Initial Update Single Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `57714596`
- Operation: Dummy-Installer-Pfad mit ersetzten Marker-Factories und Schedule-Hooks
- Messwerkzeug: `.venv/bin/python -c`
- Dummy-Widgets und Dummy-Callbacks ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Ergebnis |
| --- | --- |
| `radio_marker_initial_update_calls` | `activate,direct_schedule` |

## Ergebnisse Nachher

| Operation | Ergebnis |
| --- | --- |
| `radio_marker_initial_update_calls` | `activate` |

## Bewertung

- Der direkte zweite Initial-Update-Schedule wurde entfernt.
- Initiales Update bleibt ueber `_activate_radio_pane_marker_callbacks` erhalten.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Aussagekraft

- Die Messung prueft nur den Dummy-Pfad des Installers.
- Reale Laufzeit haengt staerker von Tk-Bindings und `after`-Scheduling ab.
