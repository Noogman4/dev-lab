---
id: "gem"
name: "gem"
command: "gem"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "gem"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 461
reviewed_at: "2026-11-13"
locally_checked_version: "RubyGems 3.4.20; nur Hilfe/Version ausgeführt"
---

# gem – Ruby-Gems und Ruby-Umgebung zusammen betrachten

## 1. Kurzbeschreibung

gem ist die RubyGems-Oberfläche. Sie verwaltet Ruby-Pakete und deren ausführbare Programme. Welche Installation betroffen ist, hängt vom gewählten Ruby und dessen Gem-Pfaden ab.

## 2. Was macht der Befehl?

Eine Gem-Spezifikation ist nicht dasselbe wie eine für ein Projekt fixierte Bundler-Auflösung. Globale, benutzerbezogene und projektspezifische Umgebungen können verschiedene Versionen enthalten. Native Erweiterungen werden gegebenenfalls kompiliert. Die aktuelle Onlinequelle beschreibt RubyGems 4.0.24, lokal wurde nur die Hilfe/Version von 3.4.20 geprüft.

Quelle, am 2026-11-13 gelesen: [RubyGems: Kommandoreferenz](https://guides.rubygems.org/command-reference/) sowie lokale gem-Hilfe

## 3. Syntax

```text
gem [GLOBALE_OPTIONEN] KOMMANDO [ARGUMENTE] [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `list --local` | Lokal bekannte Gems anzeigen. |
| `specification` | Spezifikation oder einzelne Felder lesen. |
| `install`, `uninstall` | Gem-Bestand ändern. |
| `--user-install` | In Benutzerbereich installieren; weiterhin echte Änderung. |
| `--local` | Quelle auf lokale Domain begrenzen, kein allgemeiner Schreibschutz. |
| `--norc` | Keine .gemrc laden; keine vollständige Ausführungsisolation. |
| `update --system` | RubyGems selbst aktualisieren; kein gewöhnlicher Paketbericht. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
gem list --local
```

Das Muster würde nur Gems der gewählten Ruby-Umgebung anzeigen. Es wurde nicht ausgeführt. Ein installiertes Gem muss nicht die im Projekt per Bundler aktivierte Version sein. Der getrennte Versionsaufruf prüft nur die lokale CLI-Verfügbarkeit.

### Schritt 3: Aussagegrenze festhalten

Ein Hilfe-/Versionsaufruf wird unten gesondert belegt. Er bestätigt nur die lokale Schnittstelle, nicht den Ablauf des Musters.

## 6. Typische Anwendungsfälle

**Ruby-Umgebungen verstehen:** Ruby-Version, Gem-Pfade und Projektlock unterscheiden. **Paketinformationen lesen:** Metadaten vor Build oder Installation prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Installation kann Erweiterungs-/Installationscode ausführen. Gemspecs können Ruby-Code enthalten; fremde Dateien sind keine bloßen Daten. Remote-Abfragen und Downloads sind zusätzliche Wirkungen. Keine Gems installiert, Ruby-Umgebung oder Quellen verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Gem installiert, Programm fehlt | Ruby-/Gem-Pfad und Binärpfad prüfen. |
| Falsche Version im Projekt | Bundler-Auflösung getrennt von gem list. |
| Zugriff verweigert | Kein pauschales sudo; Zielumgebung klären. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** RubyGems 3.4.20; nur Hilfe/Version ausgeführt. Praktisch geprüft: Nur Hilfe/Version ausgeführt; Beispiel, echte Netz-/Geräte-/Sitzungszugriffe und zustandsändernde Modi nicht praktisch geprüft. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ruby` | Interpreter der gewählten Umgebung. |
| `bundle` | Projektbezogene Auflösung über Bundler. |
| `gem specification` | Gezielte Metadatenansicht. |

Ausgangsdatensatz 461 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
