---
id: "setfacl"
name: "setfacl"
command: "setfacl"
category: "Benutzer & Rechte"
language: "de"
root_required: false
risk_level: "caution"
tags: ["benutzer", "rechte", "acl", "dateirechte"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 118
reviewed_at: "2026-11-13"
locally_checked_version: "acl 2.3.2 (setfacl 2.3.2)"
---

# setfacl – Zusätzliche Zugriffsrechte für einzelne Benutzer und Gruppen vergeben

## 1. Kurzbeschreibung

`setfacl` setzt, ändert und entfernt Einträge einer **Access Control List (ACL)**. Damit kannst du einer einzelnen weiteren Person oder Gruppe Rechte an einer Datei geben, ohne Eigentümer, Besitzergruppe oder die Rechte für „alle anderen“ zu ändern.

**Root-Rechte sind für eigene Dateien nicht nötig.** Laut [Debian-Manpage zu setfacl](https://manpages.debian.org/trixie/acl/setfacl.1.en.html) darf der Eigentümer einer Datei ihre ACL ändern, außerdem Prozesse mit `CAP_FOWNER` (praktisch Root). Für fremde Dateien sind deshalb Root-Rechte nötig.

## 2. Was macht der Befehl?

Jede Datei hat drei Grundeinträge (Eigentümer, Besitzergruppe, andere). `setfacl` fügt benannte Einträge hinzu, zum Beispiel `user:anna:r--`. Sobald benannte Einträge existieren, gibt es auch eine **Maske**: Sie ist die Obergrenze für benannte Benutzer, benannte Gruppen und die Besitzergruppe. `setfacl` berechnet die Maske standardmäßig automatisch neu.

Ordner können zusätzlich eine **Vorgabe-ACL** (`default:`) haben. Neu angelegte Dateien und Unterordner erben diese Einträge.

Die Wirkung siehst du mit `getfacl`; in `ls -l` erscheint ein `+` hinter den Rechten. Voraussetzung ist ein Dateisystem mit ACL-Unterstützung, etwa ext4, XFS oder Btrfs.

### Eintragsformat

| Eintrag | Bedeutung |
| --- | --- |
| `u:anna:rw` | Benutzer `anna` darf lesen und schreiben. |
| `g:projekt:rx` | Gruppe `projekt` darf lesen und betreten/ausführen. |
| `m::r` | Maske auf Lesen begrenzen. |
| `o::-` | Andere erhalten keine Rechte. |
| `d:u:anna:rwX` | Vorgabe für neue Einträge in einem Ordner. |
| `u:anna` | Ohne Rechte: Form für das Entfernen mit `-x`. |

Statt `rwx` sind auch Zahlen (4, 2, 1) erlaubt. Großes `X` setzt das Ausführrecht nur für Ordner und bereits ausführbare Dateien.

## 3. Syntax

```text
setfacl [OPTIONEN] -m EINTRÄGE DATEI ...
setfacl -x EINTRÄGE DATEI ...
setfacl --restore=SICHERUNG
```

```bash
setfacl -m u:anna:r bericht.txt
setfacl -R -m g:projekt:rwX freigabe
setfacl -d -m g:projekt:rwX freigabe
setfacl -x u:anna bericht.txt
```

Das bisherige NetMon-Beispiel `setfacl --help` zeigt nur die Hilfe; der Platzhalter `setfacl [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-m`, `--modify` | Einträge hinzufügen oder ändern. | Bestehende andere Einträge bleiben. |
| `-x`, `--remove` | Einträge entfernen. | Nicht vorhandene Einträge sind kein Fehler. |
| `-b`, `--remove-all` | Alle erweiterten Einträge entfernen. | Grundeinträge bleiben. |
| `-k`, `--remove-default` | Vorgabe-ACL entfernen. | Nur bei Ordnern relevant. |
| `--set` | ACL vollständig ersetzen. | Alte Einträge gehen verloren. |
| `-M DATEI`, `-X DATEI` | Einträge aus Datei hinzufügen bzw. entfernen. | Akzeptiert `getfacl`-Ausgabe. |
| `-d`, `--default` | Auf die Vorgabe-ACL wirken. | Für Vererbung in Ordnern. |
| `-R`, `--recursive` | Rekursiv anwenden. | Mit `X` statt `x` kombinieren. |
| `-n`, `--no-mask` | Maske nicht neu berechnen. | Für Fortgeschrittene. |
| `--test` | Ergebnis nur anzeigen, nichts ändern. | Sehr nützlich vor großen Änderungen. |
| `--restore=DATEI` | Sicherung von `getfacl -R` zurückspielen. | Setzt auch Besitz und Sonderbits, soweit erlaubt. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Einer weiteren Person Lesezugriff auf eine eigene Datei geben, das Ergebnis prüfen und wieder entfernen. Als „weitere Person“ dient das vorhandene Systemkonto `nobody`. Alle Dateien liegen in einem eigenen Übungsordner.

### Schritt 1: Übungsdatei und Sicherung

```bash
uebung="$(mktemp -d -t netmon-setfacl-XXXXXX)" || exit 1
cd "$uebung" || exit 1
mkdir projekt
printf 'x\n' > projekt/plan.txt
getfacl -R projekt > acl-sicherung.txt
```

Die Sicherung erlaubt später eine vollständige Rückkehr.

### Schritt 2: Änderung testen

```bash
setfacl --test -m u:nobody:r projekt/plan.txt
```

Ausgabe im Test: `projekt/plan.txt: u::rw-,u:nobody:r--,g::rw-,m::rw-,o::---,*`. Es wurde nichts geändert.

### Schritt 3: Eintrag setzen und prüfen

```bash
setfacl -m u:nobody:r projekt/plan.txt
ls -l projekt/plan.txt
getfacl -c projekt/plan.txt
```

`ls -l` zeigt nun ein `+`. `getfacl` listet `user:nobody:r--` und eine Maske.

### Schritt 4: Eintrag wieder entfernen

```bash
setfacl -x u:nobody projekt/plan.txt
setfacl -b projekt/plan.txt
getfacl -c projekt/plan.txt
```

Nach `-x` ist der benannte Eintrag weg, die Maske bleibt aber bestehen; `ls -l` zeigte im Test weiter ein `+`. Erst `-b` entfernt alle erweiterten Einträge.

### Schritt 5: Vorgabe-ACL für einen Ordner

```bash
setfacl -d -m g:users:rx projekt
touch projekt/neu
getfacl -c projekt/neu
```

Die neue Datei erhält `group:users:r-x`; die Maske begrenzt das wirksam auf `r--`, weil neue Dateien kein Ausführrecht haben.

## 6. Typische Anwendungsfälle

- **Einzelfreigabe:** Einer Person Lesezugriff geben, ohne eine neue Gruppe anzulegen.
- **Gemeinsamer Projektordner:** `setfacl -R -m g:projekt:rwX ordner` für den Bestand und `setfacl -R -d -m g:projekt:rwX ordner` für künftige Dateien.
- **Dienstzugriff:** Einem Dienstkonto (etwa für einen Webserver) Lesezugriff auf genau einen Ordner geben.
- **Rechte sichern und wiederherstellen:** `getfacl -R` vor großen Änderungen, `setfacl --restore` danach bei Bedarf.

## 7. Risiken, Nebenwirkungen und Vorsicht

- **Unerwartete Freigaben:** ACLs sind in `ls -l` nur am `+` erkennbar. Vergessene Einträge geben Zugriff, den niemand mehr im Blick hat.
- **Ordnerrechte nicht vergessen:** Ein Eintrag auf einer Datei nützt nichts, wenn die Person die Ordner davor nicht betreten darf (`x`). Umgekehrt öffnet `rwx` auf einem Ordner das Anlegen und Löschen von Einträgen.
- **Maske und `chmod`:** Ein späteres `chmod g-w` verändert bei erweiterter ACL die Maske und damit auch die Rechte benannter Benutzer. Im Test wurde aus `rw-` wirksam `r--`.
- **`--set` und `-b`** entfernen bestehende Einträge ohne Rückfrage.
- **Rekursion:** `-R` auf falsche Pfade ändert viele Dateien; mit `x` statt `X` werden alle Dateien ausführbar.
- **Kopieren und Sichern:** Nicht jedes Werkzeug übernimmt ACLs. Ohne passende Optionen gehen sie beim Kopieren oder Archivieren verloren.

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt bestehen.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `setfacl: Option -m: Invalid argument near character 3` | Unbekannter Benutzer- oder Gruppenname (im Test `u:gibtsnicht:r`). | Namen mit `getent passwd` bzw. `getent group` prüfen. |
| `... Invalid argument near character 11` | Ungültiges Rechtezeichen (im Test `rq`). | Nur `r`, `w`, `x`, `X`, `-` oder Ziffern. |
| `setfacl: DATEI: Operation not permitted` | Datei gehört dir nicht. | Eigentümer prüfen; nur mit Berechtigung. |
| `setfacl: DATEI: No such file or directory` | Pfad falsch. | Arbeitsordner prüfen. |
| `Operation not supported` | Dateisystem ohne ACL-Unterstützung. | Anderes Dateisystem oder Einhängeoptionen prüfen. |
| Zugriff klappt trotz Eintrag nicht | Maske, Ordnerrechte oder Sicherheitsmodul. | `getfacl` (`#effective`) und `namei -l` prüfen. |

Im Test endeten Syntaxfehler mit Rückgabewert `2`, Rechte- und Pfadfehler mit `1`. **Prüfpunkt:** Die Meldung `Operation not supported` wurde nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Vorher sichern:** `getfacl -R ordner > acl.txt`.
2. **Mit `--test` beginnen.**
3. **Gezielt `-m` und `-x` verwenden,** nicht `--set`.
4. **Bei `-R` immer `X`.**
5. **Ergebnis mit `getfacl` prüfen** und auf `#effective` achten.
6. **Vergebene ACLs dokumentieren,** damit sie später wieder entfernt werden.

### Prüfstand

- **Geprüfte Version:** setfacl 2.3.2 (Paket acl 2.3.2-1build1.1) auf ext4.
- **Tatsächlich ausgeführt** im Testordner: `-m` mit benanntem Benutzer, automatische Maske, Maskenwirkung nach `chmod g-w`, `--test`, `-x` (Maske bleibt), `-b`, `-k`, `-d -m` mit Vererbung an neue Datei, Sicherung mit `getfacl -R` und `--restore`, unbekannter Name und ungültige Rechte (Rückgabe 2), nicht vorhandene Datei (Rückgabe 1). Außerdem wurde ein `-m` auf eine fremde Systemdatei abgelehnt (`Operation not permitted`, Rückgabe 1, keine Änderung).
- **Nicht geprüft:** `-M`/`-X`, `--set`, `-n`, `-R` mit `-L`/`-P`, Dateisysteme ohne ACL-Unterstützung, Root-Aufrufe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `getfacl` | Zeigt ACLs und erstellt Sicherungen. |
| `chmod` | Ändert klassische Rechte und bei ACLs die Maske. |
| `chgrp`, `chown` | Ändern Besitzverhältnisse statt Zusatzrechte. |
| `namei -l` | Prüft Ordnerrechte entlang eines Pfads. |
| `cp -a`, `rsync -A`, `tar --acls` | Übernehmen ACLs beim Kopieren oder Archivieren. |

Ausgangseintrag: Datensatz 118 in `index.json` (`setfacl`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Eintragsformat, Maske, Vorgabe-ACL, Sicherung und einen geprüften Ablauf ersetzt.
