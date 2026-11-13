---
id: "zypper"
name: "zypper"
command: "zypper"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "zypper"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 477
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; zypper fehlt"
---

# zypper – ZYpp-Objekte und automatische Metadatenzugriffe verstehen

## 1. Kurzbeschreibung

zypper ist die CLI zu libzypp. Sie verwaltet Pakete, Patches, Patterns und Quellen. Ein Such-/Informationsauftrag kann je nach Refreshkonfiguration bereits Netz- und Cachezugriffe verursachen.

## 2. Was macht der Befehl?

Ein Patch ist eine Wartungsinformation mit betroffenen Paketversionen, ein Pattern eine Funktionsgruppe. update und dist-upgrade sind unterschiedliche Auflösungsaufträge; letztere Form kann umfassendere Anbieter-/Bestandsänderungen einschließen. Ein Dry-run prüft ohne fehlende heruntergeladene Pakete nicht automatisch alle Dateikonflikte.

Quelle, am 2026-11-13 gelesen: [openSUSE/libzypp: zypper-Handbuch](https://manpages.opensuse.org/Tumbleweed/zypper/zypper.8.en.html)

## 3. Syntax

```text
zypper [GLOBALE_OPTIONEN] KOMMANDO [KOMMANDO_OPTIONEN] [ZIELE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--no-refresh` | Automatische Repositoryaktualisierung für den Aufruf vermeiden. |
| `search`, `info` | Nach Objekten suchen beziehungsweise Details anzeigen. |
| `--type` | Objekttyp je Unterbefehl wählen. |
| `refresh` | Metadaten abrufen und Cache erzeugen. |
| `install --dry-run` | Transaktion planen; keine vollständige Paketdateiprüfung. |
| `--download-only` | Herunterladen, weiterhin Netz-/Dateiänderung. |
| `update`, `dist-upgrade`, `remove` | Bestand ändern. |
| `--non-interactive` | Rückfragen vermeiden, kein Simulationsmodus. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
zypper --no-refresh info lernpaket
```

Das erfundene Paket wird nicht angefragt. --no-refresh gehört vor den Unterbefehl. Es verhindert keine Änderung, wenn statt info ein schreibender Befehl gewählt würde. Ohne passenden Metadatenbestand bleibt das Ergebnis unvollständig.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**SUSE-Wartung verstehen:** Paket, Patch und Pattern getrennt lesen. **Transaktionen vorbereiten:** Anbieterwechsel, Entfernungen und verfügbare Prüfdaten bewusst bewerten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Paketaktionen können Skripte ausführen. Signaturprüfungen nicht abschalten und unbekannte Schlüssel nicht automatisch akzeptieren. Auf transaktionalen Systemen gelten zusätzliche Wrapper-/Snapshotregeln. Zypper fehlt lokal; keine Quellen, Caches, Locks, Snapshots oder Pakete verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Kein Treffer | Typ, Name und Cachezustand prüfen. |
| Dry-run übersieht Konflikt | Nicht vorhandene Paketdateien begrenzen Dateikonfliktprüfung. |
| Rootdateisystem schreibgeschützt | Distributionsmodell beachten, keine Remounts durchführen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; zypper fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `rpm` | Paketdaten und unterliegende Transaktion. |
| `transactional-update` | Eigenständiges Wartungsmodell. |
| `dnf` | Andere RPM-Resolveroberfläche. |

Ausgangsdatensatz 477 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
