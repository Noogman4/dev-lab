---
id: "pacman"
name: "pacman"
command: "pacman"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "pacman"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 465
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; pacman fehlt"
---

# pacman – Pacman-Operation vor den Kurzoptionen lesen

## 1. Kurzbeschreibung

pacman ist Archs libalpm-basierte Paketverwaltung. Großgeschriebene Operationsoptionen wie -Q, -S und -R bestimmen zuerst den Modus; nachfolgende Kleinbuchstaben haben darin unterschiedliche Bedeutungen.

## 2. Was macht der Befehl?

-Q bezieht sich auf installierte Pakete, -S auf Synchronisationsquellen. Ein lokales Paketarchiv kann ohne Installation abgefragt werden. Repositoryangebot und installierter Bestand sind verschiedene Datenquellen. Die typische Aktualisierung einer Rolling-Release-Umgebung ist als zusammenhängende Wartung zu planen; bloßes Auffrischen und anschließende einzelne Installation kann zu einem nicht unterstützten Teilupgrade führen.

Quelle, am 2026-11-13 gelesen: [Arch/Pacman: Projekthandbuch](https://man.archlinux.org/man/pacman.8.en)

## 3. Syntax

```text
pacman OPERATION [OPTIONEN] [ZIELE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-Qi PAKET` | Installierte Paketinformationen. |
| `-Qip DATEI` | Informationen eines lokalen Paketarchivs, keine Installation. |
| `-Ss MUSTER` | Synchronisationsdaten durchsuchen. |
| `-Syu` | Datenbanken aktualisieren und Systemupgrade durchführen. |
| `-U DATEI` | Lokales Paket installieren. |
| `-R` | Pakete entfernen; Zusatzoptionen ändern Umfang. |
| `--noconfirm` | Rückfragen umgehen; kein Schutz vor falscher Auswahl. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
pacman -Qip ./eigenes-lernpaket.pkg.tar.zst
```

Das Muster setzt ein eigenes gültiges Archiv voraus. Die Datei wurde nicht erstellt und der Aufruf nicht ausgeführt, weil pacman fehlt. -p wählt im Query-Modus eine Datei; es registriert das Paket nicht. Aus Metadaten folgt keine Vertrauenswürdigkeit des enthaltenen Codes.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Anleitungen lesen:** Operation und Unteroption als Einheit verstehen. **Pakete prüfen:** Archivbeschreibung von Installation trennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Pakettransaktionen führen Installationsskripte und Hooks aus. --nodeps, --overwrite und --noconfirm sind keine allgemeine Reparatur. Sperrdateien nicht löschen. Keine Datenbanken, Signaturschlüssel, Archive oder Paketbestände verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Option hat andere Wirkung | Zuerst -Q/-S/-R-Modus prüfen. |
| Datenbank gesperrt | Anderen Paketvorgang respektieren; keine Sperre entfernen. |
| Datei nicht als Paket lesbar | Format und Herkunft prüfen; nicht mit -U ausprobieren. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; pacman fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `pamac` | Andere libalpm-Oberfläche. |
| `paru` | AUR-Helfer mit zusätzlichen Ausführungswegen. |
| `makepkg` | Build aus PKGBUILD, echte Codeausführung. |

Ausgangsdatensatz 465 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
