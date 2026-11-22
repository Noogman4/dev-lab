---
id: "paru"
name: "paru"
command: "paru"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "paru"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 467
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; paru fehlt"
---

# paru – AUR-Helfer mit gefährlicher argumentloser Vorgabe

## 1. Kurzbeschreibung

paru ist ein AUR-Helfer und pacman-Wrapper. Laut Projektmanual bedeutet ein Aufruf ohne Argumente paru -Syu und damit einen Aktualisierungsauftrag, keine harmlose Übersicht.

## 2. Was macht der Befehl?

AUR-Pakete werden aus Community-Buildrezepten gebaut. Repositorypakete und AUR-Rezepte haben unterschiedliche Herkunft und Prüfung. Bare Suchwörter können eine interaktive Auswahl mit anschließender Installation öffnen. Deshalb werden nur ausdrücklich benannte Informationsformen als Diagnose beschrieben.

Quelle, am 2026-11-13 gelesen: [Paru-Projekt: originale Manpage](https://raw.githubusercontent.com/Morganamilo/paru/master/man/paru.8)

## 3. Syntax

```text
paru OPERATION [OPTIONEN] [ZIELE]
paru --help
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-Ss TEXT` | Suche, auf AUR erweitert; Netzabfrage möglich. |
| `-Si PAKET` | Paketinformation mit AUR-Unterstützung. |
| `-Q` | Installierten pacman-Bestand abfragen. |
| `-G` | PKGBUILD herunterladen; echte Datei-/Netzaktion. |
| `-Gp` | Rezept ausgeben statt klonen; kann trotzdem Netz benötigen. |
| `-B` | Lokales PKGBUILD bauen; Codeausführung. |
| `--aur`, `--repo` | Zielquelle begrenzen, Abhängigkeiten können andere Quellen einbeziehen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
paru -Si lernpaket
```

Das erfundene Paket wird nicht angefragt. Die Informationsform ist von paru lernpaket und einem argumentlosen Aufruf zu unterscheiden. Ein angezeigtes Rezept wäre vor dem Build mit allen Quellen und weiteren Skripten zu prüfen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**AUR-Anleitungen beurteilen:** Hilfsprogramm, Rezept und endgültige Pacman-Transaktion auseinanderhalten. **Quellen klären:** Community und Distributionspakete getrennt ausweisen.

## 7. Risiken, Nebenwirkungen und Vorsicht

PKGBUILDs können schon bei Verarbeitung Code ausführen. Helferbenutzung ersetzt kein Rezeptreview. Caches können Quellen und gebaute Archive enthalten; Cleanup kann diese löschen. Paru fehlt lokal; keine Abfragen, Downloads, Builds oder privilegierten Transaktionen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Argumentloser Start aktualisiert | Dokumentierte Vorgabe -Syu, kein Helpmodus. |
| Suchbegriff öffnet Auswahl | Interaktive Installationsfunktion statt bloßem Filter. |
| Build scheitert | Nicht als Root wiederholen; Rezept und Voraussetzungen klären. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; paru fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `pacman` | Unterliegende Pakettransaktion. |
| `yay` | Anderer AUR-Helfer mit eigener Semantik. |
| `makepkg` | Buildwerkzeug für PKGBUILD. |

Ausgangsdatensatz 467 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
