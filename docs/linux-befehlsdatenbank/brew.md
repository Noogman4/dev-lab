---
id: "brew"
name: "brew"
command: "brew"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "brew"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 454
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; brew fehlt"
---

# brew – Homebrew-Prefix und Distribution getrennt verwalten

## 1. Kurzbeschreibung

brew ist die Homebrew-Oberfläche, auch unter Linux. Sie verwaltet einen eigenen Prefix und ersetzt nicht die Paketdatenbank der Distribution. Das Programm ist hier nicht installiert.

## 2. Was macht der Befehl?

Eine Formula beschreibt ein Paket; eine Bottle ist eine vorgebaute Form. Ein Keg ist eine konkrete installierte Version im Cellar. keg-only bedeutet, dass das Paket nicht gewöhnlich in den Prefix verlinkt wird. PATH-Reihenfolge und Prefix bestimmen, welches Programm später gestartet wird. macOS-spezifische Casks sind keine allgemeine Linux-Installationsmethode.

Quelle, am 2026-11-13 gelesen: [Homebrew: brew-Handbuch](https://docs.brew.sh/Manpage)

## 3. Syntax

```text
brew KOMMANDO [OPTIONEN] [FORMULA...]
brew --version
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `list` | Installierte Formulae anzeigen. |
| `info FORMULA` | Paketinformationen; Quelle und Aktualisierung beachten. |
| `search TEXT` | Suche kann online erweitert werden. |
| `update` | Homebrew-/Tap-Metadaten aktualisieren. |
| `upgrade` | Pakete aktualisieren. |
| `install`, `uninstall` | Prefixbestand verändern. |
| `cleanup` | Versionen/Caches entfernen; kein Diagnosemodus. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
brew list --versions
```

Das nicht ausgeführte Muster würde den Homebrew-Bestand mit Versionen anzeigen. Es listet nicht den apt-/rpm-Bestand. Eine gefundene Version beweist nicht, dass genau dieses Binary zuerst im PATH steht.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Mehrere Paketwelten verstehen:** Prefix und Systempakete auseinanderhalten. **Diagnose vorbereiten:** Herkunft eines gestarteten Programms feststellen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Formulae und externe Taps enthalten ausführbare Logik. Automatische Metadatenaktualisierung, Downloads und Analytik können je nach Befehl und Konfiguration stattfinden. brew nicht pauschal mit sudo starten. Keine Homebrew-Installation, Prefix-, PATH- oder Analytikeinstellung geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Befehl trotz Installation fehlt | Prefix/Verlinkung/PATH prüfen. |
| Andere Version startet | Mehrere Installationsquellen und Reihenfolge berücksichtigen. |
| Formel unbekannt | Quelle und Namen prüfen, keine fremden Taps automatisch hinzufügen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; brew fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `apt` | Distributionspakete, anderer Bestand. |
| `command -v` | Aufrufpfad prüfen. |
| `brew info` | Formula-/Prefixinformationen. |

Ausgangsdatensatz 454 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
