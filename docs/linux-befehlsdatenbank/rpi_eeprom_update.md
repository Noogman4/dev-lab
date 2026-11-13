---
id: "rpi_eeprom_update"
name: "rpi-eeprom-update"
command: "rpi-eeprom-update"
category: "Raspberry Pi"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Raspberry Pi", "rpi-eeprom-update"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 533
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; EEPROM-Abfrage und Aktualisierung offen"
---

# rpi-eeprom-update – EEPROM-Status und Aktualisierung unterscheiden

## 1. Kurzbeschreibung

rpi-eeprom-update prüft beziehungsweise aktualisiert unterstützte Raspberry-Pi-Bootloader-EEPROMs.

## 2. Was macht der Befehl?

Der Aufruf ohne Updateoption prüft nach Herstellerimplementierung Versionsstände. Im gelesenen aktuellen Quellstand kann er als Root am Terminal bei verfügbarem Update auch eine Installationsrückfrage anbieten; er ist deshalb keine garantiert reine Statusabfrage. -a und Dateiauswahl können ein Update vorbereiten oder ausführen. Modelle, Bootmedium und Paketstand beeinflussen den Ablauf. Das Skript kann eine systemweite Defaults-Datei einlesen. Ein Statusabruf ist daher nicht mit einem isolierten Offlinevergleich gleichzusetzen.

Quelle, am 2026-11-13 gelesen: [Raspberry Pi: rpi-eeprom-update-Implementierung](https://raw.githubusercontent.com/raspberrypi/rpi-eeprom/master/rpi-eeprom-update)

## 3. Syntax

```text
rpi-eeprom-update [OPTIONEN] [DATEI]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -h | Werkzeughilfe. |
| ohne Updateoption | Versionen prüfen; reale Hardware und Konfiguration beteiligt, aktuell unter Bedingungen auch Updateangebot. |
| -a | Verfügbare Updates automatisch anwenden beziehungsweise vorbereiten. |
| -f DATEI | Bestimmtes Bootloaderabbild wählen; schreibender Ablauf möglich. |
| -r | Vorbereitete Updateartefakte entfernen; keine reine Abfrage. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
rpi-eeprom-update -h
```

Nur die Bedeutung der Hilfe wird erklärt. Hier wurde kein Skript gestartet, kein Image ausgewählt und kein Update vorbereitet.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Updateverfahren vor Wartung verstehen; Versionsprüfung und Flashvorgang auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein fehlerhaftes Firmwareupdate kann Bootfähigkeit beeinträchtigen. Stromversorgung, Modell, Image und Wiederherstellung müssen gesondert geklärt sein. Kein Flashzugriff, keine Bootdatei und kein Neustart.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Nicht unterstütztes Board | EEPROM-Modellunterstützung und Firmwarepaket prüfen. |
| Update vorgemerkt | Status ist nicht gleich erfolgreich abgeschlossener Flashvorgang. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; EEPROM-Abfrage und Aktualisierung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| vcgencmd | Andere Firmwareinformationen. |
| raspinfo | Breiter Diagnosebericht. |
| raspi-config | Weitere Systemkonfiguration. |

Ausgangsdatensatz 533 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
