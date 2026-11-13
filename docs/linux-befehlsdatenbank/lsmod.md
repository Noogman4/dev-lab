---
id: "lsmod"
name: "lsmod"
command: "lsmod"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "lsmod"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 608
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Funktionsprüfung offen"
---

# lsmod – Geladene Kernelmodule anzeigen

## 1. Kurzbeschreibung

lsmod formatiert die Liste aktuell geladener Kernelmodule.

## 2. Was macht der Befehl?

Die Daten stammen aus /proc/modules. Eingebaute Kernelbestandteile sind dort keine nachladbaren Module. Used by und Referenzzahlen beschreiben Nutzung, erlauben aber keinen sicheren Schluss, ein Modul könne gefahrlos entfernt werden.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man8/lsmod.8.html)

## 3. Syntax

```text
lsmod [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| ohne Optionen | Geladene Module anzeigen |
| --help | Implementierungshilfe |
| --version | kmod-Version anzeigen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
lsmod
```

Die reale Modulliste wurde nicht abgefragt. Beispielspalten wären Module, Size und Used by; es werden keine tatsächlichen Werte erfunden.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Modulzustand von installierten Moduldateien unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Anzeige lädt oder entlädt nichts. Keine reale Kernelinventur im Auftrag und keine Ableitung eines Entladeauftrags aus einer Nullzählung.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Modul fehlt | Kann eingebaut oder nicht geladen sein |
| Name anders | Alias und tatsächlichen Modulnamen unterscheiden |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| modinfo | Dateimetadaten |
| modprobe | Laden und Entfernen |
| depmod | Abhängigkeiten |

Ausgangsdatensatz 608 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
