---
id: "iostat"
name: "iostat"
command: "iostat"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "iostat"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 596
reviewed_at: "2026-11-13"
locally_checked_version: "Sysstat 12.6.1; nur Versionsaufruf"
---

# iostat – CPU- und Geräte-I/O-Statistiken einordnen

## 1. Kurzbeschreibung

iostat aus Sysstat zeigt CPU- und Blockgeräte-I/O-Statistiken.

## 2. Was macht der Befehl?

Der erste Bericht umfasst normalerweise die Zeit seit dem Boot, spätere Berichte das jeweilige Intervall. -y unterdrückt bei Intervallbetrieb den anfänglichen Gesamtbericht. Messwerte eines virtuellen oder geschichteten Geräts sind nicht automatisch physische Datenträgerwerte. Das Programm ist vorhanden; Geräte wurden nicht vermessen.

Quelle, am 2026-11-13 gelesen: [Sysstat: iostat-Primärhandbuch](https://man7.org/linux/man-pages/man1/iostat.1.html)

## 3. Syntax

```text
iostat [OPTIONEN] [GERÄT ...] [INTERVALL [ANZAHL]]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -x | Erweiterte Gerätekennzahlen. |
| -d | Gerätebericht. |
| -c | CPU-Bericht. |
| -y | Ersten Bericht seit Boot im Intervallbetrieb überspringen. |
| -k / -m | Übertragungsmengen skalieren; jeweilige Einheiten beachten. |
| -V | Sysstat-Version anzeigen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
iostat -x -y 1 2
```

Das Muster würde begrenzte Intervallberichte aus realen Kernelstatistiken ausgeben. Es wurde nicht ausgeführt. Eine Zeile mit hoher Auslastung wäre für sich noch kein Ursachenbeweis.

### Schritt 3: Aussagegrenze festhalten

Ein Hilfe-/Versionsaufruf wird unten gesondert belegt. Er bestätigt nur die lokale Schnittstelle, nicht den Ablauf des Musters.

## 6. Typische Anwendungsfälle

I/O-Begriffe in Diagnosen verstehen; Gesamtmittelwert und Intervallmessung unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

await enthält Warte- und Bearbeitungsanteile. %util nahe 100 beweist bei parallelen Geräten wie SSD/RAID nicht automatisch die maximale Leistungsgrenze. Keine Belastung erzeugt und keine Geräte angesprochen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Erste Zeile wirkt veraltet | Bericht seit Boot statt kurzer Intervallwert. |
| Leere Gerätespalten | Sichtbarkeit und Geräteebenen prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Sysstat 12.6.1; nur Versionsaufruf. Praktisch geprüft: Nur Hilfe/Version ausgeführt; Beispiel, echte Netz-/Geräte-/Sitzungszugriffe und zustandsändernde Modi nicht praktisch geprüft. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| vmstat | Andere Systemzeitreihe. |
| top | Prozessübersicht. |
| lsblk | Gerätebaum, gesonderte reale Abfrage. |

Ausgangsdatensatz 596 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
