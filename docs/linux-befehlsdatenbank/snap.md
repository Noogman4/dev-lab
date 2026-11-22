---
id: "snap"
name: "snap"
command: "snap"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "snap"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 473
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; snap fehlt"
---

# snap – Snap-Revision, Kanal und Dienstzustand unterscheiden

## 1. Kurzbeschreibung

snap ist die CLI des snapd-Systems. Sie verwaltet Apps und gegebenenfalls Dienste. list zeigt Installiertes, find sucht im Store; beide Datenquellen sind zu unterscheiden.

## 2. Was macht der Befehl?

Die Softwareversion stammt vom Hersteller, die Revision ist eine Storekennung. Tracking beschreibt den verfolgten Kanal. Ein Paketname allein erklärt weder laufende Prozesse noch erlaubte Schnittstellen. Snap-Confinement hängt vom Modus und verbundenen Interfaces ab; classic ist kein gleicher Schutzumfang wie strict.

Quelle, am 2026-11-13 gelesen: [Canonical: Einstieg](https://snapcraft.io/docs/tutorials/get-started/) und [Aktualisierungen](https://snapcraft.io/docs/how-to-guides/manage-snaps/manage-updates/)

## 3. Syntax

```text
snap KOMMANDO [OPTIONEN] [NAME...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `list [--all]` | Installierte beziehungsweise auch ältere Revisionen anzeigen. |
| `find` | Store-Suche; Netzabfrage. |
| `info` | Paket-/Kanalinformationen, gegebenenfalls Storezugriff. |
| `install`, `refresh`, `remove` | Bestand ändern; refresh ohne Anzeigeoption kann aktualisieren. |
| `refresh --list`, `--time` | Aktualisierungskandidaten beziehungsweise Zeitplan anzeigen. |
| `refresh --hold`, `--unhold` | Updateverhalten ändern; versionsabhängig. |
| `connections`, `connect`, `disconnect` | Schnittstellen anzeigen beziehungsweise Freigaben ändern. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
snap list --all
```

Die nicht ausgeführte Anzeige würde aktive und aufbewahrte Revisionen unterscheidbar machen. disabled bei einer alten Revision bedeutet nicht automatisch eine defekte aktive Anwendung. Eine hohe Revisionszahl lässt sich nicht pauschal als höhere Softwareversion interpretieren.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Bestand verstehen:** Version, Revision und Kanal getrennt erfassen. **Berechtigungen beurteilen:** Appmodus und verbundene Interfaces vor einem Start prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Installation und Refresh können Dienste schalten; Revert kann Konfigurationsdaten ändern, ohne alle gemeinsamen Nutzdaten zurückzusetzen. Hold verhindert je nach Zielauswahl nicht jede explizite Aktualisierung. Snap fehlt hier; kein snapd-Start, Storezugriff oder Systemeingriff.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| cannot communicate with server | Dienstvoraussetzung prüfen; hier nicht starten. |
| Alte Revision disabled | Aufbewahrter Stand, nicht zwingend Fehler. |
| Hold blockiert gezielten Refresh nicht | Dokumentierte Ziel-/Hold-Semantik beachten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; snap fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `snapd` | Verwaltungsdienst. |
| `flatpak` | Anderes App-/Runtime-Modell. |
| `snap connections` | Ressourcenfreigaben anzeigen. |

Ausgangsdatensatz 473 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
