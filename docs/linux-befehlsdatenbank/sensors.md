---
id: "sensors"
name: "sensors"
command: "sensors"
category: "Hardware"
language: "de"
root_required: false
risk_level: "caution"
tags: ["sensors", "hardware"]
status: "Keine Sensorabfrage oder Setzaktion ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 393
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale lm-sensors-Manpage gelesen"
---

# sensors – bereitgestellte Messwerte lesen, ohne Grenzwerte zu setzen

## 1. Kurzbeschreibung

`sensors` zeigt Messwerte unterstützter Hardwaremonitoringquellen. Dazu können Temperaturen, Spannungen und Drehzahlen gehören. **Für übliche bereitgestellte Lesewerte sind keine Root-Rechte nötig.**

## 2. Was macht der Befehl?

Die lokale Manpage beschreibt die Verwendung vorhandener Sensorchips und Konfiguration. Ein Wert erhält seine Bedeutung erst durch Quelle, Kanal, Einheit und gegebenenfalls Kalibrierung.

`sensors` ist von `sensors-detect` zu unterscheiden. Die normale Anzeige bedeutet nicht automatisch eine umfassende aktive Suche nach unbekannten Chips. Außerdem besitzt `sensors` mit `-s` eine ausdrücklich verändernde Funktion.

## 3. Syntax

```bash
sensors
sensors -u
sensors -j
```

Die letzte Form ist in der lokalen Manpage als JSON-Ausgabe beschrieben. Keine tatsächlichen Messwerte dieses Rechners wurden für den Eintrag erhoben.

## 4. Wichtige Optionen

| Option | Aufgabe | Grenze |
| --- | --- | --- |
| `-u` | Rohbezeichnungen und Werte zeigen. | Erfordert korrekte Kanalzuordnung. |
| `-j` | JSON ausgeben. | Datentypen und Quelle erhalten. |
| `-f` | Fahrenheit statt Celsius. | Einheit bei Vergleichen beachten. |
| `-c DATEI` | Konfiguration auswählen. | Rechen-/Bezeichnungsregeln beeinflussen Ausgabe. |
| `-s` | Konfigurierte Setzanweisungen anwenden. | Benötigt Root; keine reine Anzeige. |
| `--help` | Bedienung. | Kein Messlauf erforderlich. |

## 5. Beispiel erklärt Schritt für Schritt

Ein geplanter `sensors -u`-Aufruf würde die Daten mit ihren Rohkanälen zeigen. Er wurde hier nicht ausgeführt.

Angenommen, ein fiktiver Wert beträgt `45`. Ohne Kanal und Einheit ist er kaum aussagekräftig. Als Temperatur in Celsius wäre er anders zu bewerten als ein falsch zugeordneter Spannungs- oder Drehzahlwert.

Auch ein angezeigter Grenzwert ist nicht automatisch die passende allgemeine Empfehlung für jedes Gerät. Quelle und Herstellerkontext beachten, bevor eine Änderung erwogen wird.

## 6. Typische Anwendungsfälle

- Eine bekannte Messquelle im Verlauf betrachten.
- Temperatur- und Drehzahlangaben sauber benennen.
- Eine Konfigurationszuordnung verstehen.
- Maschinenlesbare Werte für eine begrenzte lokale Anzeige vorbereiten.

## 7. Risiken, Nebenwirkungen und Vorsicht

`-s` kann Grenzwerte aus der Konfiguration setzen. Nicht zur vermeintlichen Aktualisierung einer Anzeige ergänzen.

Falsche Sensorzuordnung kann unnötige Eingriffe oder übersehene echte Probleme verursachen. Ein einzelner Wert ohne Zeit, Quelle und Lastkontext reicht für weitgehende Aussagen selten aus.

## 8. Häufige Fehler

- **`-s` als Scan lesen:** Es ist die Setzfunktion.
- **Einheiten vermischen:** Celsius und Fahrenheit unterscheiden.
- **Kein Wert gleich fehlender Sensor:** Treiber und Freigaben können fehlen.
- **Rohkanal als bekannten Bauteilnamen behandeln:** Zuordnung prüfen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit der normalen Anzeige und klar benannten Quellen beginnen. Eine automatische Chip-Erkennung ist kein notwendiger Folgeschritt jeder fehlenden Anzeige.

Keine Lüfter- oder Grenzwertkonfiguration ändern, bevor Bauteil und zulässiger Bereich eindeutig bekannt sind.

## 10. Verwandte Befehle

- `sensors-detect`: Aktive Erkennung mit eigenen Risiken.
- `acpi`: Weitere Energie-/Temperaturquellen.
- `upower`: Energiegeräte.
- `fancontrol`: Lüftersteuerung mit anderer Wirkung.

**Prüfstand:** Lokale Manpage gelesen. Keine Messung, Grenzwertsetzung oder Lüfteränderung ausgeführt.

Ausgangsdatensatz 393 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
