---
id: "ethtool"
name: "ethtool"
command: "ethtool"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "ethtool"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 427
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# ethtool – Treiber- und Linkinformationen gezielt unterscheiden

## 1. Kurzbeschreibung

ethtool fragt Eigenschaften von Netzwerktreibern und Geräten ab und kann sie verändern. Ein lesender Gerätebericht ist weder ein Durchsatztest noch eine Aufforderung, Linkparameter zu setzen.

## 2. Was macht der Befehl?

Unterstützte, angebotene und aktuell ausgehandelte Linkmodi sind verschieden. Die angezeigte Geschwindigkeit beschreibt den Link, nicht den nutzbaren Internetdurchsatz. Treiberspezifische Statistiknamen sind nicht herstellerübergreifend normiert. Ein Zählerstand braucht einen Messzeitraum für eine Rate; ein einzelner Fehlerzähler erklärt noch keine Ursache.

Quelle, am 2026-11-13 gelesen: [ethtool-Projekthandbuch](https://man7.org/linux/man-pages/man8/ethtool.8.html)

## 3. Syntax

```text
ethtool GERAET
ethtool {-i|-k|-S} GERAET
ethtool -s GERAET PARAMETER
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `GERAET` | Linkeigenschaften anzeigen. |
| `-i` | Treiber- und Firmwareinformationen. |
| `-k` / `-K` | Offload-Features anzeigen / ändern; Großschreibung entscheidend. |
| `-S` | Geräte-/Treiberstatistiken; Umfang abhängig von Unterstützung. |
| `-s` | Linkparameter verändern. |
| `-r` | Autonegotiation neu starten. |
| `-t ... offline` | Geräteselbsttest, kann Betrieb unterbrechen; kein Offline-Dateitest. |
| `--version` | Nur Programmversion ausgeben. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
ethtool -i eth-lernen
```

Der erfundene Gerätename steht für eine ausdrücklich ausgewählte Schnittstelle. -i würde deren Treiberinformationen anfordern, nicht Firmware aktualisieren. Ein Versionsstring allein beweist nicht, dass ein bestimmtes Feature auf dieser Hardware funktioniert.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Inventarisierung:** Treiber und Firmware dem richtigen Gerät zuordnen. **Störungen untersuchen:** Linkstatus, Featureanzeige und Zähler getrennt bewerten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Setzen von Geschwindigkeit, Duplex, Offloads, EEPROM oder Firmware kann Verkehr unterbrechen oder Hardware dauerhaft verändern. Rechte hängen vom konkreten Modus ab. Nicht unterstützte Diagnose ist kein Anlass, einen schreibenden Selbsttest zu versuchen. Keine Hardwareoperation wurde ausgeführt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Operation not supported | Treiber unterstützt die Anfrage nicht; Versions- und Hardwaregrenzen dokumentieren. |
| Unknown speed | Kein verwertbarer ausgehandelter Wert; nicht mit null Durchsatz gleichsetzen. |
| Groß-/Kleinschreibung verwechselt | -k liest, -K ändert. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ip link` | Allgemeiner Linkzustand. |
| `lspci` | Bus-/Geräteidentifikation. |
| `iperf3` | Aktive Ende-zu-Ende-Messung, andere Aussage. |

Ausgangsdatensatz 427 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
