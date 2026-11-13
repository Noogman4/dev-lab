---
id: "vmstat"
name: "vmstat"
command: "vmstat"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "vmstat"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 618
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Funktionsprüfung offen"
---

# vmstat – Systemstatistik als begrenzte Zeitreihe lesen

## 1. Kurzbeschreibung

vmstat zeigt Prozess-, Speicher-, Paging-, I/O- und CPU-Kennzahlen.

## 2. Was macht der Befehl?

Die erste Zeile hat bei Raten üblicherweise Bezug auf die Zeit seit Boot; spätere Zeilen auf das Intervall. Prozess- und Speicherfelder sind dagegen Momentaufnahmen. r zählt ausführbare Aufgaben, b blockierte; si/so beziehen sich auf Swap, nicht sämtliches Paging.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man8/vmstat.8.html)

## 3. Syntax

```text
vmstat [OPTIONEN] [INTERVALL [ANZAHL]]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -w | Breite Ausgabe |
| -t | Zeitstempel |
| -S EINHEIT | Speicherskalierung |
| -y | Erste Zeile überspringen |
| -s | Ereignissummen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
vmstat -w 1 3
```

Drei begrenzte Berichte wären vorgesehen; keine reale Messung ausgeführt. Der erste Bericht dürfte nicht unbesehen als 1-Sekunden-Fenster gelesen werden.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Zeitbasis und Messgröße in Leistungsdiagnosen unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Container- und Hostsicht können auseinanderfallen. Keine Cache-, Swap- oder Ressourcenänderung vorgenommen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Endlosausgabe | Anzahl ausdrücklich setzen |
| Zahlen scheinen widersprüchlich | Einheiten und Zeitbasis vergleichen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| free | Speicherübersicht |
| sar | Historie |
| iostat | Gerätewerte |

Ausgangsdatensatz 618 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
