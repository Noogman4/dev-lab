---
id: "free"
name: "free"
command: "free"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "free"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 592
reviewed_at: "2026-11-13"
locally_checked_version: "procps-ng 4.0.4; nur Versionsaufruf"
---

# free – Arbeitsspeicherwerte richtig lesen

## 1. Kurzbeschreibung

free zeigt zusammengefasste RAM- und Swapinformationen aus /proc/meminfo.

## 2. Was macht der Befehl?

free und available sind unterschiedliche Spalten. available schätzt Speicher, der neuen Anwendungen ohne Auslagern zur Verfügung stehen könnte; Caches sind teilweise rückgewinnbar. Das gelesene procps-ng-Handbuch berechnet used als total minus available. Diese Definition ist versionsgebunden und nicht aus beliebigen älteren Tabellen zu übernehmen.

Quelle, am 2026-11-13 gelesen: [procps-ng: free-Handbuch](https://man7.org/linux/man-pages/man1/free.1.html); lokales Handbuch und Hilfe gelesen

## 3. Syntax

```text
free [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -h | Lesbare Einheiten. |
| -b | Bytes ausgeben. |
| -m | Mebibytes; nicht pauschal dezimale MB. |
| --si | Dezimale Skalierung berücksichtigen. |
| -s SEKUNDEN | Wiederholte Anzeige. |
| -c ZAHL | Wiederholungszahl begrenzen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
free -h
```

Die Tabelle wird hier nur beschrieben. Ausgeführt wurde die Versionshilfe, keine reale Speicheraufnahme. Ein hoher Cacheanteil allein wäre kein Beweis für Speichermangel.

### Schritt 3: Aussagegrenze festhalten

Ein Hilfe-/Versionsaufruf wird unten gesondert belegt. Er bestätigt nur die lokale Schnittstelle, nicht den Ablauf des Musters.

## 6. Typische Anwendungsfälle

Speicherbegriffe verstehen; RAM und Swap getrennt lesen; Messergebnisse aus einer passenden Umgebung einordnen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Containergrenzen und sichtbare Hostdaten können auseinanderfallen. Summierte RAM-und-Swap-Werte sind kein einheitlich schneller Speicher. Keine Cachebereinigung, Swapänderung oder Belastung.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Wenig free, viel available | Rückgewinnbare Anteile erklären den Unterschied. |
| Zahlen anders als ältere Anleitung | Version und Skalierung prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** procps-ng 4.0.4; nur Versionsaufruf. Praktisch geprüft: Nur Hilfe/Version ausgeführt; Beispiel, echte Netz-/Geräte-/Sitzungszugriffe und zustandsändernde Modi nicht praktisch geprüft. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| pmap | Prozessabbildungen. |
| top | Prozesswerte. |
| vmstat | Weitere Zeitreihen. |

Ausgangsdatensatz 592 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
