---
id: "cargo"
name: "cargo"
command: "cargo"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "cargo"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 455
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; cargo fehlt"
---

# cargo – Rust-Projekte statt Systempakete verwalten

## 1. Kurzbeschreibung

cargo ist Rusts Projekt-, Build- und Paketwerkzeug. Abhängigkeiten eines Projekts und mit cargo install bereitgestellte Programme sind verschiedene Bestände. Cargo fehlt lokal; nichts wurde nachinstalliert.

## 2. Was macht der Befehl?

Cargo.toml beschreibt das Projekt und Versionsanforderungen, Cargo.lock die konkret aufgelösten Versionen. Ein Build kann build.rs und prozedurale Makros ausführen. Auch ein Test ist damit Ausführung von Projektcode, keine harmlose Metadatenanzeige. Die lokal gewählte Toolchain und Konfiguration beeinflussen das Ergebnis.

Quelle, am 2026-11-13 gelesen: [Rust-Projekt: Cargo-Kommandos](https://doc.rust-lang.org/cargo/commands/cargo.html) und [cargo metadata](https://doc.rust-lang.org/cargo/commands/cargo-metadata.html)

## 3. Syntax

```text
cargo [OPTIONEN] KOMMANDO [ARGUMENTE]
cargo metadata --format-version 1 --no-deps --offline
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `metadata` | Projekt-/Abhängigkeitsinformationen als JSON. |
| `--no-deps` | Metadaten auf Workspace-Pakete begrenzen. |
| `--offline` | Netzwerkzugriff vermeiden; vorhandener Cache muss reichen. |
| `--locked` | Veränderung/Neuerstellung des Lockfiles untersagen. |
| `--frozen` | Locked und offline kombinieren, soweit für den Befehl unterstützt. |
| `build`, `test`, `run` | Kompilieren und gegebenenfalls Code ausführen. |
| `install` | Ausführbare Programme in Cargo-Installationsbereich installieren. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
cargo metadata --format-version 1 --no-deps --offline --locked
```

Das Muster setzt einen eigenen bereits vorbereiteten Workspace mit passendem Lockfile voraus. --format-version legt das JSON-Schema fest; --locked kann statt einer stillen Änderung abbrechen. Ohne lokalen Cargo-Stand wurde auch diese Metadatenform nicht ausgeführt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Rust-Abhängigkeiten verstehen:** Manifestanforderungen und Lockauflösung trennen. **Builds planen:** Toolchain, Cache und ausführbare Buildbestandteile dokumentieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Offline ist kein Schreibschutz und kein Schutz vor lokal ausgeführtem Buildcode. Fremde Projekte können Konfiguration, Runner oder Buildskripte enthalten. Keine fremden Workspaces gebaut, Programme installiert oder Cargo-/Toolchain-Caches verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Lockfile müsste aktualisiert werden | Mit --locked bewusst abbrechen; Ursache prüfen. |
| Offline fehlt Paket | Cacheinhalt reicht nicht; keine automatische Netzfreigabe. |
| cargo fehlt | Offene praktische Prüfung, keine stillschweigende Toolchaininstallation. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; cargo fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `rustc` | Compiler der ausgewählten Toolchain. |
| `rustup` | Toolchainverwaltung, eigenes Änderungsrisiko. |
| `npm` | Anderes sprachbezogenes Paketökosystem. |

Ausgangsdatensatz 455 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
