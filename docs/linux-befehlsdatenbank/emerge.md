---
id: "emerge"
name: "emerge"
command: "emerge"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "emerge"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 459
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; emerge fehlt"
---

# emerge – Portage-Planung und Buildausführung unterscheiden

## 1. Kurzbeschreibung

emerge ist die Portage-Oberfläche von Gentoo. Ohne abweichende Aktion ist die Anforderung eines Pakets grundsätzlich ein Merge-/Installationsauftrag, keine reine Suche.

## 2. Was macht der Befehl?

Atome beschreiben Paketbedingungen einschließlich Kategorie, Version oder Slot; Sets werden mit @ gekennzeichnet. USE-Flags beeinflussen Funktionen und Abhängigkeiten. world steht für einen definierten Satz von System- und Nutzerwünschen, nicht einfach jede installierte Datei. Der gelesene Projektmanualstand ist historisch; lokale aktuelle Optionen müssen gesondert geprüft werden.

Quelle, am 2026-11-13 gelesen: [Gentoo/Portage: emerge-Projekthandbuch](https://dev.gentoo.org/~zmedico/portage/doc/man/emerge.1.html)

## 3. Syntax

```text
emerge [OPTIONEN] [AKTION] [ATOM|@SET...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--search` | Paketmetadaten durchsuchen. |
| `--pretend`, `-p` | Geplante Aktionen anzeigen statt Merge. |
| `--ask`, `-a` | Vor Fortsetzung fragen; kein allgemeiner Offline-Modus. |
| `--verbose`, `-v` | Zusätzliche Plan-/USE-Details. |
| `--sync` | Repository aktualisieren; Netz-/Dateiänderung. |
| `--depclean` | Nicht benötigte Pakete entfernen; kein Cacheputzen. |
| `--unmerge` | Entfernen ohne gewöhnliche Abhängigkeitsauflösung; besonders vorsichtig. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
emerge --pretend --verbose app-misc/lernpaket
```

Das erfundene Atom enthält Kategorie und Paketname. --pretend ist bewusst Teil der nicht ausgeführten Planform. Die Auflösung könnte wegen fehlendem Paket, Maskierung oder USE-Konflikten abbrechen. Ein lesbarer Plan ist kein erfolgreicher Buildtest.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Gentoo-Anleitungen verstehen:** Atom, Slot, USE und Set auseinanderhalten. **Wartung vorbereiten:** Gesamte Paket-/Flagänderung vor Build und Merge bewerten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ebuilds und Buildschritte führen Code aus. Sync, Merge und depclean verändern Bestand oder Metadaten. Eine Bestätigung schützt nicht vor einem falsch verstandenen Plan. emerge fehlt hier; keine Repositories synchronisiert, Builds gestartet oder Pakete entfernt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Paket maskiert | Grund und Profil prüfen, nicht automatisch demaskieren. |
| USE-Konflikt | Anforderungen verstehen statt globale Flags blind ändern. |
| depclean entfernt Gewünschtes | world-/Abhängigkeitsbeziehung prüfen; Vorschlag nicht automatisch ausführen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; emerge fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `portageq` | Portagebezogene Abfragen. |
| `ebuild` | Einzelne Buildphasen, echte Codeausführung. |
| `equery` | Zusatzwerkzeug, nicht überall installiert. |

Ausgangsdatensatz 459 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
