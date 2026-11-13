---
id: "modinfo"
name: "modinfo"
command: "modinfo"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "modinfo"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 610
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Funktionsprüfung offen"
---

# modinfo – Metadaten einer Moduldatei lesen

## 1. Kurzbeschreibung

modinfo liest Metadaten aus Kernelmodulen und lädt sie nicht.

## 2. Was macht der Befehl?

Ein Modulname wird im gewählten Modulbaum aufgelöst; ein Dateipfad wählt eine konkrete Datei. Vermagic, Parameter und Lizenz sind Metadaten, kein Nachweis sicherer Hardwarefunktion oder vertrauenswürdiger Herkunft.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man8/modinfo.8.html)

## 3. Syntax

```text
modinfo [OPTIONEN] MODULNAME oder DATEI
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -F FELD | Ein Metadatenfeld |
| -p | Parameterbeschreibungen |
| -n | Dateiname |
| -k VERSION | Anderen Kernelstand auswählen |
| -0 | NUL-Trenner |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
modinfo -F vermagic EIGENE_MODULDATEI.ko
```

Das Muster benötigt eine eigene gültige Moduldatei und wurde nicht ausgeführt. Es lädt keinen Treiber, belegt aber auch keine Ladefähigkeit.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Moduldatei und geladenen Treiber unterscheiden; Parameter vor einer Änderung verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Keine fremden Kerneldateien als Testfixture kopieren. Modulsignaturanzeige allein ist keine vollständige Vertrauenskette.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Module not found | Suchversion und Pfad prüfen |
| Feld leer | Nicht jedes Modul hat alle Metadaten |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| lsmod | Geladene Module |
| modprobe | Aktives Laden |
| depmod | Abhängigkeiten |

Ausgangsdatensatz 610 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
