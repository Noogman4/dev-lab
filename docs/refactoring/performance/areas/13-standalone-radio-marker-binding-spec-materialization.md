# 13 Standalone Radio Marker Binding Spec Materialization Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `d9a3dff1`
- Operation: Update- und Grip-Bindings mit Dummy-Callbacks erstellen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Pfad ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `standalone_radio_marker_binding_spec_materialization_before` | 0.6737667029997283 s |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `standalone_radio_marker_binding_spec_materialization_after` | 0.2230273440000019 s |

## Bewertung

- Direkte Tuple-Erzeugung ist fuer diesen Micro-Pfad schneller als Generator- und `zip`-Materialisierung.
- Die absolute Laufzeit bleibt klein und betrifft nur Marker-Setup-Code.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.

## Moegliche spaetere Optimierungen

- Keine weitere Optimierung empfohlen.
- Laufzeitrelevanter ist echte Tk-Binding-Arbeit.

## Aussagekraft

- Die Messung prueft nur das Erstellen der Binding-Tuples.
- Reale Laufzeit haengt staerker von Tk-Event-Binding ab.
