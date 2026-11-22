---
id: "rawshark"
name: "rawshark"
command: "rawshark"
category: "Wireshark & Analyse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Wireshark & Analyse", "rawshark"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 709
reviewed_at: "2026-11-13"
locally_checked_version: "Hilfe Wireshark 4.2.2 gelesen; keine Paketverarbeitung"
---

# rawshark – Rawshark-Eingabeformat ausdrücklich festlegen

## 1. Kurzbeschreibung

rawshark wertet Roh-Paketströme mit vorgegebener Kapselung aus.

## 2. Was macht der Befehl?

Im Unterschied zu tshark -r nimmt es Format und Kapselung nicht automatisch passend an. -d und -r sind erforderlich; -s überspringt einen Pcap-Dateikopf. Der 24-Byte-Pcap-Kopf allein genügt nicht: Byteordnung der Datensatzfelder muss zur laufenden Architektur passen; -p erwartet das plattformabhängige pcap_pkthdr-Layout. Pcapng ist damit kein beliebig austauschbarer Datenstrom. -F wählt auszuwertende Felder.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://www.wireshark.org/docs/man-pages/rawshark.html)

## 3. Syntax

```text
rawshark -d encap:TYP -r DATEI [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -d encap:TYP | Linkschicht vorgeben |
| -r DATEI | Datei oder Pipe |
| -s | Pcap-Dateikopf überspringen |
| -F FELD | Analysefeld |
| -n | Namensauflösung abschalten |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
rawshark -n -s -d encap:1 -r EIGENE_KLASSISCHE_PCAP -F frame.len
```

Die lokale Hilfe wurde gelesen, der Musterlauf aber nicht ausgeführt. Kapselungs- und Headerkompatibilität bleiben praktisch offen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Spezielle Streamanalyse von allgemeiner Capturedateianalyse unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Falsche Headerannahmen verfälschen Dekodierung. Keine echten Pipes, Pakete oder Namensauflösung verwendet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Keine sinnvollen Felder | Kapselung und Feldauswahl prüfen |
| Datei nicht erkannt | Nicht jede Captureart ist Rawshark-Eingabe |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Hilfe Wireshark 4.2.2 gelesen; keine Paketverarbeitung. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| tshark | Allgemeiner Dateileser |
| capinfos | Dateiformat |
| od | Rohbytes |

Ausgangsdatensatz 709 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
