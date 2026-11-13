---
id: "vcgencmd"
name: "vcgencmd"
command: "vcgencmd"
category: "Raspberry Pi"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Raspberry Pi", "vcgencmd"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 534
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Firmwarewerte und Gerätepfade offen"
---

# vcgencmd – Firmwareinformationen gezielt abfragen

## 1. Kurzbeschreibung

vcgencmd kommuniziert mit der Raspberry-Pi-Firmware; der Unterbefehl bestimmt die Wirkung.

## 2. Was macht der Befehl?

Unterstützte Unterbefehle unterscheiden sich nach Board und Firmware. measure_temp liefert eine SoC-Sensortemperatur, keine vollständige thermische Diagnose. get_throttled enthält eine Bitmaske mit aktuellen und seit dem Start aufgetretenen Zuständen. Eine einzelne Hexzahl ist deshalb nicht pauschal als aktuelle Störung zu lesen.

Quelle, am 2026-11-13 gelesen: [Raspberry Pi OS: vcgencmd-Referenz](https://www.raspberrypi.com/documentation/computers/os.html#vcgencmd)

## 3. Syntax

```text
vcgencmd UNTERBEFEHL [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| commands | Unterstützte Befehle erfragen. |
| version | Firmware-Buildinformationen. |
| measure_temp | SoC-Temperatur lesen. |
| measure_clock arm | Aktuellen Arm-Takt abfragen. |
| get_throttled | Aktuelle und historische Statusbits lesen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
vcgencmd measure_temp
```

Eine Ausgabe wie temp=42.0 ist nur ein erfundenes Schema, kein Messwert dieser Umgebung; die tatsächliche Darstellung enthält eine Temperatureinheit. Kein Gerät wurde angesprochen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Gezielte Diagnose statt vollständigem Bericht vorbereiten; Temperatur und Drosselstatus unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Nicht jeden Firmwarebefehl als lesend behandeln. Zugriffsrechte auf Mailbox-Geräte nicht für einen Test erweitern. Unterstützung und Interpretation auf konkretem Board prüfen. Kein vcgencmd vorhanden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Device file fehlt | Kein passendes Gerät oder Treiberzugriff. |
| Unbekannter Unterbefehl | Firmwareunterstützung prüfen. |
| Historisches Bit gesetzt | Von aktuell gesetzten Zustandsbits unterscheiden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Firmwarewerte und Gerätepfade offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| raspinfo | Umfassende Sammlung. |
| rpi-eeprom-update | Bootloader-EEPROM separat. |
| free | Arbeitsspeicher auf Linux-Ebene. |

Ausgangsdatensatz 534 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
