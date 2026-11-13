---
id: "guix"
name: "guix"
command: "guix"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "guix"]
status: "Ausgearbeitet; Primärquelle nur in Indexauszügen gelesen; Struktur geprüft; zur Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 462
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; guix fehlt; vollständiger Primärquellenabruf offen"
---

# guix – Guix-Profilgenerationen ohne System-Rollback-Verwechslung

## 1. Kurzbeschreibung

guix verwaltet Software in Profilen und bietet weitere getrennte System-/Entwicklungsfunktionen. Hier wird guix package behandelt. Guix fehlt lokal; die offizielle Website und PDF lieferten Zugriffsfehler.

## 2. Was macht der Befehl?

Als tatsächlich lesbare Primärbelege dienen die Suchindex-Auszüge des offiziellen GNU-Guix-Handbuchs: Sie zeigen list-installed, list-generations und roll-back sowie die Erzeugung neuer Profilgenerationen. Die vollständige aktuelle Handbuchseite konnte nicht geöffnet werden. Diese begrenzte Quellenlage bleibt ein offener Reviewpunkt; darüber hinausgehende Optionszusagen werden hier nicht behauptet.

Quelle, am 2026-11-13 gelesen: [GNU Guix: offizielles Handbuch, gelesene Suchindex-Auszüge; Vollabruf 403](https://guix.gnu.org/manual/en/guix.pdf)

## 3. Syntax

```text
guix package --list-installed
guix package --list-generations
guix package --roll-back
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `package --list-installed` | Pakete des ausgewählten Profils auflisten. |
| `package --list-generations` | Profilgenerationen anzeigen. |
| `package --roll-back` | Zur vorherigen Profilgeneration wechseln; echte Änderung. |
| `--profile` / `-p` | Profil ausdrücklich wählen; genaue lokale Syntax nachprüfen. |
| `pull` | Guix-/Paketdefinitionsstand aktualisieren; kein bloßer Bericht. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
guix package --list-installed
```

Die Zeile ist nicht ausgeführt. Ein Profilbericht wäre keine Liste aller Programme des Hosts. Ein Profilwechsel wäre auch keine vollständige Wiederherstellung veränderlicher Benutzerdateien. Diese Grenzen sind bei jeder späteren Anwendung gesondert zu prüfen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Guix-Begriffe einordnen:** Profilbestand und Generation verstehen. **Review vorbereiten:** Vollständige Primärseite und installierte Schnittstelle nachholen, bevor weitere Optionen übernommen werden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Profiländerungen können Downloads oder Builds und neue Programmstände bewirken. Ein Rollback ist selbst eine Änderung; er wird hier nicht als Beispiel ausgeführt. Keine Guix-Dienste, Profile, Storeinhalte oder Benutzerkonfiguration angelegt oder verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Handbuch nicht abrufbar | Quellenprüfung begrenzt; Volltextreview offen dokumentieren. |
| Anderes Profil zeigt anderen Bestand | Profilwahl und aufgerufene Umgebung unterscheiden. |
| Rollback als Backup gedeutet | Veränderliche Nutzdaten brauchen eine eigene Sicherungsstrategie. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; guix fehlt; vollständiger Primärquellenabruf offen. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `guix package` | Profilbezogene Paketverwaltung. |
| `guix pull` | Definitions-/Guix-Stand aktualisieren. |
| `nix-env` | Anderes Profilökosystem mit eigener Semantik. |

Ausgangsdatensatz 462 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
