---
id: "acpi"
name: "acpi"
command: "acpi"
category: "Hardware"
language: "de"
root_required: false
risk_level: "safe"
tags: ["acpi", "hardware"]
status: "Distributions-Manpage geprüft; keine Sensordaten erhoben"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 380
reviewed_at: "2026-11-13"
locally_checked_version: "acpi lokal nicht installiert"
---

# acpi – Akku-, Netzteil- und Temperaturangaben lesen

## 1. Kurzbeschreibung

`acpi` zeigt vom System bereitgestellte Energie- und Temperaturinformationen. Es ist kein Werkzeug zum Flashen der Firmware oder zum Verändern von Lüfterkurven. **Für übliche lesbare Statusdaten sind keine Root-Rechte nötig.**

## 2. Was macht der Befehl?

Die [Debian-Manpage zu acpi](https://manpages.debian.org/trixie/acpi/acpi.1.en.html) beschreibt Informationen aus `/sys` beziehungsweise der älteren `/proc`-Schnittstelle. Welche Werte erscheinen, hängt von Hardware, Kernel und Firmware ab.

Ein fehlender Akku auf einem Desktop ist normal. Eine nicht vorhandene Temperaturquelle beweist ebenfalls keinen defekten Sensor. Erst klären, welche Informationen diese Plattform überhaupt bereitstellt.

## 3. Syntax

```bash
acpi -b
acpi -a
acpi -t
```

Die Formen wählen Akku, Netzteil oder Temperatur. Sie schalten kein Gerät aus und ändern keine Energiesparrichtlinie.

## 4. Wichtige Optionen

| Option | Auswahl | Grenze |
| --- | --- | --- |
| `-b` | Akkuinformationen. | Nicht jede Plattform hat einen Akku. |
| `-a` | Netzteilstatus. | Nicht der Internet- oder Funkstatus. |
| `-t` | Temperaturangaben. | Nur bereitgestellte Quellen. |
| `-c` | Kühlgeräteinformationen. | Keine automatische Lüftersteuerung. |
| `-i` | Zusätzliche Details. | Nur soweit verfügbar. |
| `-V` | Alle beschriebenen Geräteklassen. | Großes V bedeutet hier nicht Version. |
| `-v` | Programmversion. | Kleines v beachten. |
| `-h` | Hilfe. | Kein Hardwareinventurauftrag. |

## 5. Beispiel erklärt Schritt für Schritt

```bash
acpi -b
```

Ein späterer Aufruf würde den verfügbaren Akkuzustand zeigen. Das Programm ist lokal nicht installiert; es wurde kein tatsächlicher Prozentwert oder Restzeitwert gemessen.

Eine fiktive Restzeit wäre eine Schätzung aus aktuellem Zustand und Verbrauch. Sie ist keine Garantie, dass der Rechner exakt so lange weiterläuft. Wechselnde Last kann die Prognose verändern.

Vor Schlussfolgerungen Wert, Einheit und Quelle gemeinsam lesen. Ein Batteriezustand ist nicht automatisch eine Aussage über das gesamte Energiemanagement.

## 6. Typische Anwendungsfälle

- Einen aktuellen Akkustand kurz nachschlagen.
- Netzteil- und Akkubetrieb unterscheiden.
- Vorhandene thermische Quellen überblicken.
- Einen Energiebericht mit begrenzten eigenen Werten ergänzen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der beschriebene Statuszugriff ist lesend. Das größere Risiko ist die Fehlinterpretation von Schätzungen oder unvollständigen Quellen.

Aus einem einzelnen Temperaturwert nicht ohne Sensorzuordnung eine Überhitzungsdiagnose ableiten. Für Grenzwerte und Betriebsverhalten sind Gerät und Herstellerangaben relevant.

## 8. Häufige Fehler

- **Kein Akku gleich Fehler:** Plattform berücksichtigen.
- **`-V` als Version:** Hier breite Geräteausgabe.
- **Restzeit als feste Zusage:** Lastabhängige Schätzung.
- **Fehlender Wert gleich Hardwaredefekt:** Schnittstellenunterstützung prüfen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer einzelnen Datenklasse beginnen. Keine Energiespar-, Treiber- oder Firmwareeinstellung ändern, nur um eine erwartete Anzeige zu erzwingen.

Für eine integrierte Desktopansicht kann `upower` zusätzliche Geräteinformationen bieten. Dessen Angaben ebenfalls mit Quelle und Zeitpunkt betrachten.

## 10. Verwandte Befehle

- `upower`: Energiegeräte über den Systemdienst lesen.
- `sensors`: Hardwaremonitoringwerte.
- `inxi -B`: Akkuübersicht, soweit unterstützt.

**Prüfstand:** Handbuch gelesen. Keine Sensorabfrage, Installation oder Energieeinstellung ausgeführt.

Ausgangsdatensatz 380 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
