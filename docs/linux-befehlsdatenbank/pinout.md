---
id: "pinout"
name: "pinout"
command: "pinout"
category: "Raspberry Pi"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Raspberry Pi", "pinout"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 530
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Diagramm und Board-Erkennung nicht ausgeführt"
---

# pinout – GPIO-Belegung als Diagramm nachschlagen

## 1. Kurzbeschreibung

pinout aus GPIO Zero stellt die Pinbelegung eines Raspberry-Pi-Modells dar.

## 2. Was macht der Befehl?

Ein Diagramm erklärt Anschlussbezeichnungen, setzt aber keine Pins. Ohne explizite Revision wird das lokale Board ermittelt. Ein mit -r gewähltes Modell muss nicht dem angeschlossenen Gerät entsprechen. Eine physische Position ist von BCM-Nummer und Stromversorgungsanschluss zu unterscheiden.

Quelle, am 2026-11-13 gelesen: [GPIO Zero: pinout-Handbuch](https://gpiozero.readthedocs.io/en/stable/cli_pinout.html)

## 3. Syntax

```text
pinout [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -r REVISION | Bestimmten Board-Revisionscode statt Autodetektion verwenden. |
| -m | Monochrome Darstellung. |
| -c | Farbdarstellung erzwingen. |
| -h | Hilfe anzeigen. |
| -x | Browser mit pinout.xyz öffnen; kein reiner Terminalabruf. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
pinout -r REVISIONSCODE -m
```

REVISIONSCODE ist ein Platzhalter für einen zuvor aus der Herstellerreferenz bestimmten Code. Die Ausgabe wäre ein Modelldiagramm, kein elektrischer Funktionstest.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Pinbelegung vor dem Lesen einer Schaltung verstehen; Modelle anhand ihrer Header vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein richtig gezeichnetes Diagramm bestätigt weder Verkabelung noch sichere Spannungen. Remote-GPIO-Konfiguration kann einen anderen Kontext auswählen. GPIO Zero und pinout sind hier nicht vorhanden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Board unbekannt | Revisionscode und unterstützte Datenbankversion prüfen. |
| Diagramm passt nicht | Explizite Revision und tatsächliches Board getrennt abgleichen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Diagramm und Board-Erkennung nicht ausgeführt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| gpio | WiringPi-Zugriff auf Pins. |
| dtoverlay | Hardwarebeschreibung ergänzen. |
| raspinfo | Breitere Diagnose mit zusätzlichen Zugriffen. |

Ausgangsdatensatz 530 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
