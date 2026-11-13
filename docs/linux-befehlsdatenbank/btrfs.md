---
id: "btrfs"
name: "btrfs"
command: "btrfs"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "btrfs"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 211
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; btrfs fehlt"
---

# btrfs – Btrfs-Unterbefehle und ihre Eingriffe unterscheiden

## 1. Kurzbeschreibung

`btrfs` ist die Verwaltungswerkzeugsammlung für Btrfs-Dateisysteme. Die Untergruppe bestimmt, ob nur Informationen gelesen oder Daten verändert werden. Für administrative Operationen sind häufig besondere Rechte nötig; Hilfe benötigt kein Root.

## 2. Was macht der Befehl?

Ein Unterbefehl folgt auf eine Gruppe, etwa `subvolume` oder `filesystem`. Gruppen und kurze Optionen sind nicht beliebig austauschbar. In Skripten vollständige Namen verwenden: Abkürzungen können nach einem Versionswechsel mehrdeutig werden. `check` prüft offline Strukturen; `scrub` ist eine andere Prüfung. Eine Reparatur ist keine normale Fortsetzung einer fehlgeschlagenen Anzeige. Die aktuellen Projektseiten beschreiben einen veränderlichen Stand, nicht eine lokal nachgewiesene Version.

Quelle, am 2026-11-13 gelesen: [Btrfs-Hauptwerkzeug](https://btrfs.readthedocs.io/en/latest/btrfs.html), [Btrfs check](https://btrfs.readthedocs.io/en/latest/btrfs-check.html)

## 3. Syntax

```text
btrfs [GLOBALE_OPTIONEN] GRUPPE UNTERBEFEHL [OPTIONEN] [ARGUMENTE]
btrfs check --readonly GERAET
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--help`, `--version` | Hilfe beziehungsweise Programmversion; keine Dateisystemprüfung. |
| `subvolume` | Untervolumes verwalten; Erstellen und Löschen sind Änderungen. |
| `filesystem` | Dateisystemoperationen; nicht jede ist lesend. |
| `check --readonly` | Strukturprüfung ohne Reparatur; kann weitere Geräte desselben Dateisystems einbeziehen. |
| `check --repair` | Gefährliche Reparatur; Projekt warnt ausdrücklich vor unberatener Verwendung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Anforderung festlegen

Einsteiger sollen zunächst entscheiden, ob sie nur die Befehlshilfe verstehen oder tatsächlich einen Datenträger warten wollen. Hier gilt ausschließlich Dokumentationsarbeit. `btrfs` ist lokal nicht vorhanden; es wird nichts installiert.

### Schritt 2: Syntax lesen

Das zweite Syntaxmuster bedeutet eine lesende Offline-Strukturprüfung an einem ausdrücklich bestimmten Ziel. Es wird nicht ausgeführt. `--readonly` ersetzt weder die eindeutige Zielwahl noch eine unabhängige Sicherung. Auch ein angegebener einzelner Gerätepfad kann zu einem mehrteiligen Btrfs-Dateisystem gehören.

### Schritt 3: Ergebnis einordnen

Ein Status 0 würde erfolgreichen Abschluss dieser Operation bedeuten, nicht künftige Ausfallsicherheit. Ein Fehler ist zunächst ein Diagnosebefund. Daraus darf kein automatischer Wechsel auf `--repair` folgen. Es wird keine fiktive lokale Erfolgsausgabe behauptet.

## 6. Typische Anwendungsfälle

**Struktur verstehen:** Untervolumes und Dateisystemgrenzen anhand einer vorhandenen Dokumentation unterscheiden.

**Wartung planen:** Die passende Untergruppe erst nach Bestimmung von Dateisystem, Mountzustand und Ziel auswählen. Snapshots allein sind keine unabhängigen Sicherungen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Geräteoperationen, Subvolume-Löschung, Empfang von Datenströmen und Reparaturen können Daten verändern oder verlieren lassen. Ein Offline-Check kann viel RAM und I/O benötigen. Schutzprüfungen nicht mit `--force` umgehen. Keine realen Geräte, Mounts oder Reparaturen in dieser Übung.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Mehrdeutiger Unterbefehl | Abkürzung passt zu mehreren Namen; vollständige Schreibweise und lokale Hilfe verwenden. |
| Prüfung läuft lange | Metadatenumfang und Prüfmodus beeinflussen Ressourcen; nicht blind abbrechen und reparieren. |
| Fehler trotz Spiegelung | Strukturprüfung, Datenprüfung und Reparatur unterscheiden; kein Gesundnachweis aus Einzelmeldungen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Die Dokumentation der konkreten Untergruppe lesen, bevor deren Optionen benutzt werden. Für jede spätere Systemaktion ist ein eigener zulässiger Wartungsablauf nötig.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; btrfs fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `mkfs.btrfs` | Legt ein Dateisystem an und ist destruktiv. |
| `findmnt` | Zeigt Mountbeziehungen. |
| `btrfs scrub` | Andere Prüffunktion; eigener Umfang und mögliche Reparaturwirkung. |

Ausgangsdatensatz 211 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
