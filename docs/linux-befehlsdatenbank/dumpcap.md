---
id: "dumpcap"
name: "dumpcap"
command: "dumpcap"
category: "Wireshark & Analyse"
language: "de"
root_required: false
risk_level: "danger"
tags: ["Wireshark & Analyse", "dumpcap"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 705
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; keine Interface- oder Capturefunktion ausgeführt"
---

# dumpcap – Live-Capture als echten Netzwerkzugriff erkennen

## 1. Kurzbeschreibung

dumpcap zeichnet Pakete von einer Capturequelle in eine Datei auf.

## 2. Was macht der Befehl?

Das Werkzeug ist für Aufzeichnung und nicht für allgemeine Offlineanalyse gedacht. -i wählt ein Interface oder eine andere Capturequelle. Ohne bewusste Auswahl kann eine Vorgabe verwendet werden. Snaplen und Ringpuffer beeinflussen Datenumfang und Aufbewahrung.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://www.wireshark.org/docs/man-pages/dumpcap.html)

## 3. Syntax

```text
dumpcap [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -i QUELLE | Capturequelle |
| -w DATEI | Ausgabedatei |
| -f FILTER | Capturefilter |
| -c ANZAHL | Paketgrenze |
| -a duration:SEKUNDEN | Zeitgrenze |
| -p | Kein Promiscuous-Modus, weiterhin echte Aufzeichnung |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
dumpcap -i FREIGEGEBENES_TESTINTERFACE -c 5 -w NEUE_DATEI
```

Dieses Muster wurde nicht ausgeführt. Es wurde auch kein echtes Interface zur Probe aufgelistet und keine Capability gesetzt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Aufzeichnungsparameter vor einem später ausdrücklich freigegebenen Mitschnitt verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Auch ohne Promiscuous-Modus werden reale Pakete gelesen. Rechte, Einwilligung, Datenumfang und Ziel müssen zum Auftrag passen. Kein Live-Capture.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Permission denied | Keine pauschalen Setcap- oder Sudoänderungen |
| Keine Pakete | Quelle und Filter prüfen, nicht unbegrenzt mitschneiden |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; keine Interface- oder Capturefunktion ausgeführt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| tshark | Offlineanalyse mit -r |
| capinfos | Metadaten |
| wireshark | GUI |

Ausgangsdatensatz 705 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
