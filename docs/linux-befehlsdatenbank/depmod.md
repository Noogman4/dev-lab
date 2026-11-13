---
id: "depmod"
name: "depmod"
command: "depmod"
category: "Systeminformationen"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Systeminformationen", "depmod"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 590
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Modulbaum und Indexerzeugung ungeprüft"
---

# depmod – Abhängigkeiten von Kernelmodulen erzeugen

## 1. Kurzbeschreibung

depmod analysiert Kernelmodule und erzeugt Abhängigkeits- und Zuordnungsdateien.

## 2. Was macht der Befehl?

Der Standardlauf schreibt unter dem ausgewählten Modulbaum. Das ist keine reine Systeminventur. depmod lädt selbst keine Module wie modprobe, beeinflusst aber deren spätere Auflösung. Modulbaum und Kernelversion müssen zusammenpassen.

Quelle, am 2026-11-13 gelesen: [kmod: depmod-Primärhandbuch](https://man7.org/linux/man-pages/man8/depmod.8.html)

## 3. Syntax

```text
depmod [OPTIONEN] [KERNELVERSION] [MODULDATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -a | Alle ausgewählten Module auswerten. |
| -A | Nur bei Bedarf neu erzeugen. |
| -n | Ausgabe auf Standardausgabe statt regulärer Indexdateien; reale Eingabedaten werden dennoch gelesen. |
| -b BASIS | Anderen Basisbaum wählen. |
| -e | Unaufgelöste Symbole melden. |
| -F DATEI | Kernel-Symbolkarte berücksichtigen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
depmod -n -b EIGENER_MODULBAUM TEST_KERNELVERSION
```

Das Muster wäre nur mit einem eigenen passenden Modulbestand sinnvoll. Es wurde nicht ausgeführt. Eine erfundene Versionszeichenfolge liefert keinen gültigen Kompatibilitätsnachweis.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Modulindexierung in Paketierungsabläufen verstehen; depmod von Laden und Entladen unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Falsche Indizes können spätere Modulauflösung beeinträchtigen. Keine produktiven Modulbäume oder Bootdateien bearbeiten. Kein Modul geladen, entladen oder indexiert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Module directory fehlt | Kernelversion und Basisbaum prüfen. |
| Unresolved symbol | Passenden Kernelbuild und Symbolinformationen prüfen, nicht einfach erzwingen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Modulbaum und Indexerzeugung ungeprüft. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| modprobe | Module laden, gesonderte Systemwirkung. |
| modinfo | Metadaten. |
| lsmod | Geladene Module anzeigen. |

Ausgangsdatensatz 590 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
