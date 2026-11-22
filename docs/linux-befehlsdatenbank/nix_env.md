---
id: "nix_env"
name: "nix-env"
command: "nix-env"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "nix-env"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 463
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; nix-env fehlt"
---

# nix-env – Klassische Nix-Profile und Store unterscheiden

## 1. Kurzbeschreibung

nix-env verwaltet klassische Nix-Benutzerumgebungen. Ein Profil ist eine Sicht auf Storepfade; im Store vorhandene Software und im aktuellen Profil verfügbare Software sind verschiedene Mengen.

## 2. Was macht der Befehl?

Generationen erlauben das Wechseln zwischen Profilständen. query zeigt standardmäßig die aktuelle Generation; query --available betrachtet die aktive Nix-Ausdrucksquelle. Die neue nix profile-Schnittstelle ist nicht einfach dieselbe Syntax und kann ein anderes Manifestformat benutzen. Katalogkennung nix_env und tatsächlicher Programmname nix-env bleiben eindeutig zugeordnet.

Quelle, am 2026-11-13 gelesen: [Nix-Projekt: nix-env](https://nix.dev/manual/nix/latest/command-ref/nix-env.html) und [query](https://nix.dev/manual/nix/latest/command-ref/nix-env/query)

## 3. Syntax

```text
nix-env OPERATION [OPTIONEN] [SELEKTOREN]
nix-env --query --installed [--json]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--query`, `-q` | Paketinformationen abfragen. |
| `--installed` | Aktuelle Profilgeneration; Standard der Abfrage. |
| `--available`, `-a` | Angebot der aktiven Ausdrucksquelle. |
| `--profile PFAD` | Betroffenes Profil wählen. |
| `--install`, `--upgrade`, `--uninstall` | Profilbestand ändern. |
| `--list-generations` | Generationen anzeigen. |
| `--rollback` | Profilgeneration wechseln. |
| `--dry-run` | Vorschau unterstützter Änderungsoperationen; keine universelle Netzsperre. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
nix-env --query --installed --json
```

Der nicht ausgeführte Aufruf würde das aktuelle klassische Profil als JSON beschreiben. Er ist kein Inventar aller Nix-Storeobjekte. Im Store vorhandene Outputs können zu anderen Profilen oder alten Generationen gehören.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Profile verstehen:** Angebot, Storevorhandensein und aktuelle Auswahl trennen. **Migration planen:** Manifest- und CLI-Generation ausdrücklich prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Profiländerungen können Builds und Substitutdownloads auslösen. Ausdrücke können externe Quellen referenzieren. Generationenlöschen und Garbage Collection betreffen Aufbewahrung; Rollback ersetzt kein Nutzdatenbackup. Nix fehlt lokal, keine Profile oder Storepfade angelegt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Manifestformat nicht unterstützt | nix profile und nix-env nicht blind mischen. |
| Paket nicht im Profil | Storevorhandensein ist ein anderer Zustand. |
| Muster unerwartet breit | Selektoren sind reguläre Ausdrücke; genau zitieren. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; nix-env fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `nix profile` | Neuere Profiloberfläche. |
| `nix-store` | Storeverwaltung, eigenes Änderungsrisiko. |
| `guix` | Anderes funktionales Paketökosystem. |

Ausgangsdatensatz 463 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
