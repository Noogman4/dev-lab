---
id: "dtparam"
name: "dtparam"
command: "dtparam"
category: "Raspberry Pi"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Raspberry Pi", "dtparam"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 528
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; dtparam-Wirkung offen"
---

# dtparam – Parameter des Basis-Device-Trees verstehen

## 1. Kurzbeschreibung

dtparam kann zur Laufzeit Parameter des Raspberry-Pi-Basisbaums anwenden.

## 2. Was macht der Befehl?

Die Kommandozeile ist von einer dtparam=-Zeile in config.txt zu unterscheiden. Die Laufzeitvariante erzeugt ein Overlay und verändert damit den aktiven Gerätebaum. Parameter eines benannten Overlays gehören bei dessen Laden zu dtoverlay und nicht nachträglich beliebig zu dtparam.

Quelle, am 2026-11-13 gelesen: [Raspberry Pi: Dynamic Device Tree und dtparam](https://www.raspberrypi.com/documentation/computers/configuration.html#dynamic-device-tree)

## 3. Syntax

```text
dtparam -h
dtparam PARAMETER=WERT
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -h | Hilfe des Werkzeugs anzeigen. |
| ohne Parameter | Hilfe bekannter Basisbaumparameter laut Hersteller. |
| PARAMETER=WERT | Laufzeitparameter anwenden; Systemänderung. |
| Entfernung per Index | Bei Laufzeitparametern nicht mit einem Namen verwechseln. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
dtparam -h
```

Das unausgeführte Hilfemuster erklärt den Einstieg. Es setzt insbesondere keinen I2C- oder SPI-Parameter und bestätigt keine Hardwarefunktion.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Unterschied zwischen Bootkonfiguration und Laufzeitkonfiguration verstehen; Basisparameter vor einer gesonderten Änderung prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Aktivierung oder Abschaltung von Schnittstellen kann angeschlossene Hardware betreffen. Nicht alle Subsysteme reagieren gleichermaßen auf Laufzeitänderungen. Rootrechte können nötig sein. Kein Parameter angewendet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Parameter unbekannt | Basisbaum, Overlayparameter und Version auseinanderhalten. |
| Kein Effekt zur Laufzeit | Unterstützung des betroffenen Subsystems prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; dtparam-Wirkung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| dtoverlay | Benanntes Overlay samt Parametern. |
| raspi-config | Konfigurationsoberfläche. |
| gpio | GPIO-Zugriff einer anderen Werkzeugsammlung. |

Ausgangsdatensatz 528 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
