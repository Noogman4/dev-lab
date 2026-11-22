---
id: "mountpoint"
name: "mountpoint"
command: "mountpoint"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "safe"
tags: ["Datentraeger & Dateisysteme", "mountpoint"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 235
reviewed_at: "2026-11-13"
locally_checked_version: "mountpoint from util-linux 2.39.3"
---

# mountpoint – Einen Mountpunkt prüfen, ohne etwas einzuhängen

## 1. Kurzbeschreibung

`mountpoint` prüft, ob ein Pfad im eigenen Mount-Namespace als Mountpunkt geführt wird. Es mountet und unmountet nichts. Für erreichbare eigene Verzeichnisse sind keine Root-Rechte nötig.

## 2. Was macht der Befehl?

Ein Verzeichnis kann auf einem eingehängten Dateisystem liegen, ohne selbst dessen Einhängepunkt zu sein. Ein negativer Mountpunkttest bedeutet daher nicht, dass der Inhalt ohne Dateisystem gespeichert wäre. Die Implementierung liest Mountinformationen des eigenen Prozesses; andere Namespaces können anders aussehen. Die Gerätekennzahl major:minor ist eine Kennung des Kernels, keine Hardware-Seriennummer.

Quelle, am 2026-11-13 gelesen: [mountpoint-Handbuch](https://manpages.debian.org/trixie/util-linux/mountpoint.1.en.html) und lokale Manpage

## 3. Syntax

```text
mountpoint [-q | -d] PFAD
mountpoint -x BLOCKGERAET
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-q` | Keine Textausgabe; Ergebnis über Status auswerten. |
| `-d` | Gerätekennzahl des zugehörigen Dateisystems ausgeben. |
| `-x` | Gerätekennzahl eines Blockgeräts ausgeben; anderer Prüfgegenstand. |
| `--nofollow` | Letztes Pfadelement nicht als Symlink verfolgen. |
| `--version` | Programmversion anzeigen. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und util-linux. Ein neues Unterverzeichnis wird angelegt, aber nie gemountet.

### Schritt 1: Verzeichnis erzeugen und Status auffangen

```bash
uebung="$(mktemp -d -t netmon-mountpoint-XXXXXX)" || exit 1
mkdir "$uebung/ordner"
if mountpoint -q "$uebung/ordner"; then
  printf 'Eigener Mountpunkt\n'
else
  ergebnis=$?
  printf 'Status: %s\n' "$ergebnis"
  test "$ergebnis" -eq 32
fi
```

### Schritt 2: Rückgabewert erklären

Erwartet wird `Status: 32`, weil dieser frische Unterordner kein eigener Mountpunkt ist. Die if-Verzweigung verhindert, dass eine Shell mit Fehlerabbruch den erwarteten negativen Test als ungeplanten Abbruch behandelt.

### Schritt 3: Fehler vom negativen Befund trennen

Status 0 bedeutet Mountpunkt, Status 32 kein Mountpunkt und Status 1 einen Aufruf-, Rechte- oder Systemfehler. Ein Skript darf nicht jeden von null verschiedenen Wert als sicheren Nicht-Mount interpretieren. Der Übungsordner bleibt bestehen.

## 6. Typische Anwendungsfälle

**Skriptabfrage:** Vor einem später gesondert erlaubten Arbeitsschritt prüfen, welche Art von Pfad vorliegt. **Fehlerdiagnose:** Exakten Mountpunkt von beliebigen Unterordnern unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Eine Prüfung ist nur eine Momentaufnahme und sperrt den Pfad nicht. Nachträgliche Mountänderungen sind möglich. Kein negativer Befund erlaubt das Löschen eines Verzeichnisbaums. Die Zusatzoption -x wurde hier nicht an echten Geräten getestet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Ordner enthält Dateien, Test trotzdem negativ | Er liegt unter einem Mountpunkt, ist aber kein eigener. |
| Keine Ausgabe | Mit -q beabsichtigt; Status auswerten. |
| Symlink führt zu anderem Ergebnis | Pfadauflösung und --nofollow bewusst unterscheiden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Rückgabewerte unmittelbar sichern. Keine echten Mounts erzeugen, nur um einen positiven Testfall zu erzwingen. Für umfassendere Beziehungen findmnt verwenden.

**Prüfstand am 2026-11-13:** mountpoint from util-linux 2.39.3. Praktisch geprüft: Negativer Test am eigenen frischen Unterordner erfolgreich. Positive Mountfälle, --nofollow, -x und andere Namespaces nicht praktisch geprüft. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `findmnt` | Zeigt Mountquelle und übergeordnete Zuordnung. |
| `mount` | Verändert Mountzustand. |
| `stat` | Metadaten eines Pfads anzeigen. |

Ausgangsdatensatz 235 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
