---
id: "wipefs"
name: "wipefs"
command: "wipefs"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "wipefs"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 250
reviewed_at: "2026-11-13"
locally_checked_version: "wipefs from util-linux 2.39.3"
---

# wipefs – Signaturen anzeigen, ohne sie zu löschen

## 1. Kurzbeschreibung

`wipefs` erkennt Dateisystem-, RAID- und Partitionstabellensignaturen und kann sie löschen. Ohne Löschoption wird am angegebenen Ziel eine Liste erzeugt. Für das eigene Abbild benötigt die Anzeige kein Root; echte Geräte haben eigene Rechtebedingungen.

## 2. Was macht der Befehl?

Das Entfernen von Erkennungssignaturen ist keine vollständige Löschung aller gespeicherten Daten. Ein Dateisystem kann danach trotzdem unzugänglich sein. Auch GPT kann mehrere Signaturpositionen haben. Ausgabeoffsets sind Bytepositionen; sie sind nicht automatisch Blocknummern eines Dateisystems.

Quelle, am 2026-11-13 gelesen: [wipefs-Handbuch](https://manpages.debian.org/trixie/util-linux/wipefs.8.en.html)

## 3. Syntax

```text
wipefs [ANZEIGEOPTIONEN] ZIEL ...
wipefs --all ZIEL ...
wipefs --offset BYTEPOSITION ZIEL ...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--output SPALTEN` | Ausgewählte Felder anzeigen; Großbuchstabe -O, nicht -o. |
| `-J` | JSON-Ausgabe anfordern. |
| `-a`, `--all` | Alle passenden sichtbaren Signaturen löschen. |
| `-o OFFSET` | Signatur an dieser Byteposition löschen; kein Ausgabeformat. |
| `-n`, `--no-act` | Schreibaufruf auslassen; übrige Verarbeitung bleibt. |
| `-b`, `--backup` | Signaturbytes sichern, gewöhnlich im Heimatordner oder gewählten Verzeichnis. |
| `-f` | Auch gegen Schutzbedingungen löschen; niemals Lernstandard. |
| `-t TYPEN` | Auswahl von angezeigten oder gelöschten Signaturen beschränken. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash, coreutils, e2fsprogs und util-linux. Es wird nur ein frisch erstelltes eigenes ext2-Abbild gelesen, kein Gerät und kein Löschmodus.

### Schritt 1: Abbild und Prüfsumme erzeugen

### Schritt 2: Signaturen listen, anschließend Bytegleichheit nachweisen

```bash
uebung="$(mktemp -d -t netmon-wipefs-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
truncate -s 16M fs.img
mkfs.ext2 -q -E nodiscard fs.img
sha256sum fs.img > vorher.sha256
wipefs --output TYPE,OFFSET fs.img
sha256sum -c vorher.sha256
```

### Schritt 3: Ausgabe einordnen

Erwartet wird ein ext2-Treffer mit Offset, lokal `0x438`, sowie `fs.img: OK` vom Prüfsummenvergleich. Das bestätigt unveränderte Abbildbytes bei genau diesem Anzeigeaufruf. Die Position 0x438 entspricht 1080 dezimalen Bytes und gehört zur Erkennungssignatur, nicht zum Beginn des gesamten Dateisystems. Dateien und Prüfsumme bleiben erhalten.

## 6. Typische Anwendungsfälle

**Mehrdeutige Signaturen verstehen:** Vor einer gesonderten Wartungsentscheidung erkennen, welche Erkennungsmerkmale gespeichert sind. **Abbilddiagnose:** Reine Anzeige mit vor/nach-Prüfsumme von Löschmodi unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Löschen macht Daten nicht sicher vernichtet, kann aber Gerätezuordnung und Mountfähigkeit zerstören. Bei Partitionstabellenlöschung kann ein Kernel-Neueinlesen folgen. Signaturbackup ersetzt keine Nutzdatensicherung. Kein --all, --offset, --force oder Wiederherstellungs-Schreiblauf durchgeführt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Dateisystem nach -a nicht mehr erkannt | Signaturen entfernt, nicht alle Inhalte sicher gelöscht. |
| Falscher -o-Wert | Offset statt Ausgabeoption; -O/--output unterscheiden. |
| Mehrere Treffer | Mehrere Signaturen/Positionen; keine automatische Löschentscheidung. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zum Lernen nur ausdrücklich gewählte Anzeigespalten benutzen. Vor und nach einer Anzeige eigene Abbildbytes vergleichen; diesen Nachweis nicht auf andere Optionen übertragen.

**Prüfstand am 2026-11-13:** wipefs from util-linux 2.39.3. Praktisch geprüft: Nur Signaturanzeige der eigenen ext2-Datei; SHA-256 blieb gleich. Nicht praktisch geprüft: Signaturlöschung, Geräte, Cache-/Kernelnebenwirkungen und Wiederherstellung. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `blkid` | Erkennung und Kennungen abfragen. |
| `sha256sum` | Hier unveränderte eigene Abbilddatei prüfen. |
| `mkfs` | Neue Strukturen schreiben, keine Signaturanzeige. |

Ausgangsdatensatz 250 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
