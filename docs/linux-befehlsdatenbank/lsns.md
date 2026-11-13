---
id: "lsns"
name: "lsns"
command: "lsns"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "lsns"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 609
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Funktionsprüfung offen"
---

# lsns – Namespaces lesend auflisten

## 1. Kurzbeschreibung

lsns zeigt zugängliche Linux-Namespaces mit ihren Kennungen.

## 2. Was macht der Befehl?

Die Namespace-ID ist eine Inodekennung, keine PID. Daten kommen überwiegend aus /proc und können für unprivilegierte Benutzer unvollständig sein. Persistente Namespaces ohne sichtbaren Prozess erfordern besondere Berücksichtigung. Die Anzeige betritt keinen Namespace.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man8/lsns.8.html)

## 3. Syntax

```text
lsns [OPTIONEN] [NAMESPACE_ID]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -t ART | Namespaceart filtern |
| -p PID | Namespaces eines Prozesses |
| -o SPALTEN | Felder ausdrücklich wählen |
| -J | JSON-Ausgabe |
| -P | Nur prozesslose persistente Namespaces auswählen; keine Garantie vollständiger Sichtbarkeit |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
lsns -t ipc -o NS,TYPE,NPROCS,PID
```

Die echte Namespaceinventur bleibt unausgeführt; Kennungen sind keine Freigabe für nsenter.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Namespaces und Prozesszugehörigkeit verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Prozessargumente können vertraulich sein. Keine Namespaces erzeugt, betreten oder gelöscht.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Unvollständige Liste | Sichtbarkeit und Rechte beachten |
| ID ungültig | Lebensdauer und Art prüfen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| nsenter | Aktiv betreten |
| lsipc | IPC-Inhalt |
| ps | Prozessdaten |

Ausgangsdatensatz 609 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
