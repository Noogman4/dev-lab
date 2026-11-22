---
id: "fsck"
name: "fsck"
command: "fsck"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "fsck"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 220
reviewed_at: "2026-11-13"
locally_checked_version: "fsck from util-linux 2.39.3"
---

# fsck – Prüfer auswählen, ohne einen Trockenlauf mit Reparatur zu verwechseln

## 1. Kurzbeschreibung

`fsck` ist ein Verteiler an dateisystemspezifische Prüfer wie `fsck.ext4`. Es ist keine für alle Dateisysteme gleich funktionierende Reparatur. Der echte Einsatz benötigt passende Zielrechte und einen Wartungsplan; der gezeigte reine Planaufruf braucht kein Root.

## 2. Was macht der Befehl?

Optionen des Verteilers und Optionen des aufgerufenen Prüfers unterscheiden sich. `-N` führt den Prüfer nicht aus; ein kleines `-n` ist dagegen kein universeller Trockenlauf dieses Verteilers. Ohne explizite Ziele kann fsck Einträge aus fstab verarbeiten. Ein erfolgreicher Distributoraufruf beweist nicht, dass ein Dateisystem geprüft oder repariert wurde.

Quelle, am 2026-11-13 gelesen: [fsck-Handbuch](https://manpages.debian.org/trixie/util-linux/fsck.8.en.html)

## 3. Syntax

```text
fsck [VERTEILEROPTIONEN] [DATEISYSTEM ...] [-- PRUEFEROPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-N` | Nur geplante Prüferaufrufe anzeigen, nicht ausführen. |
| `-t TYP` | Dateisystemtyp beziehungsweise Auswahlfilter festlegen. |
| `-A` | fstab-Einträge gesammelt prüfen; kein Lernstandard. |
| `-M` | Gemountete Ziele überspringen; kann dafür Status 0 liefern. |
| `-s` | Prüfer nacheinander starten. |
| `-V` | Ausführliche Ablaufanzeige, keine reine Versionsoption. |
| `--version` | Programmversion anzeigen; Schreibweise beachten. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash, util-linux und ein lokal auffindbarer ext4-Prüfer. Die leere Datei ist absichtlich kein Dateisystem und darf nur mit `-N` behandelt werden.

### Schritt 1: Ausschließlich eigene Planungsdaten anlegen

```bash
uebung="$(mktemp -d -t netmon-fsck-plan-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
: > fstab.test
: > leer.bin
FSTAB_FILE="$uebung/fstab.test" fsck -N -t ext4 "$uebung/leer.bin"
```

### Schritt 2: Plan lesen

Erwartet wird eine Zeile mit `fsck.ext4` und dem eigenen vollständigen Pfad zu `leer.bin`; Versions- und Präfixtexte können variieren. `FSTAB_FILE` verweist nur für diesen Prozess auf die eigene leere Tabelle.

### Schritt 3: Aussage begrenzen

Kein Prüfer wurde ausgeführt. Entfernen von `-N` wäre eine wesentlich andere Aktion und ist kein Folgeschritt dieser Übung. Die Datei bleibt leer und der Übungsordner erhalten.

## 6. Typische Anwendungsfälle

**Prüfketten verstehen:** Dispatcher und eigentlichen Dateisystemprüfer trennen. **Startkonfiguration lesen:** fstab-Reihenfolge und Passnummern einordnen. **Automatisierung planen:** Zielwahl und Auswertungsstatus ausdrücklich behandeln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Unbekannte Optionen können an Prüfer weitergereicht werden. Automatische Reparaturoptionen haben implementierungsspezifische Bedeutung. Statusbits 1 (korrigiert), 2 (Neustart), 4 (unkorrigiert), 8 (Betriebsfehler), 16 (Aufruffehler), 32 (Abbruch) und 128 (Bibliotheksfehler) sind nicht einfach gleichartige Fehlercodes; mehrere Ergebnisse werden bitweise verknüpft. Keine aktiven Datenträger prüfen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Keine Prüfung trotz Status 0 | -N plant nur; -M kann Ziele überspringen. |
| Prüfer nicht gefunden | Typ oder Installation fehlt; keine andere Reparatur auf Verdacht. |
| Option tut je Dateisystem anderes | Lokales Handbuch des konkreten Prüfers lesen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zum Lernen -N groß schreiben, Typ und eigenes Ziel ausdrücklich angeben. Umfangreiche systemspezifische Optionen direkt im zuständigen Handbuch prüfen.

**Prüfstand am 2026-11-13:** fsck from util-linux 2.39.3. Praktisch geprüft: Nur -N-Plan mit eigener leerer Tabelle und eigener leerer Datei ausgeführt. Keine Strukturprüfung oder Reparatur; echte Prüferläufe, Statusbits und Parallelverhalten offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `e2fsck` | Eigentlicher ext-Prüfer. |
| `xfs_repair` | Eigenständige XFS-Reparatur. |
| `findmnt` | Geplante und aktive Mounttabellen ansehen. |

Ausgangsdatensatz 220 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
