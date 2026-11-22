---
id: "userdel"
name: "userdel"
command: "userdel"
category: "Benutzer & Rechte"
language: "de"
root_required: true
risk_level: "danger"
tags: ["benutzer", "konten", "kontenverwaltung", "shadow"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 124
reviewed_at: "2026-11-13"
locally_checked_version: "shadow 4.13 (Paket passwd 1:4.13+dfsg1-4ubuntu3.2); nur Hilfe und Meldungstexte"
---

# userdel – Benutzerkonto löschen (Basiswerkzeug)

## 1. Kurzbeschreibung

`userdel` entfernt ein Benutzerkonto aus `/etc/passwd`, `/etc/shadow` und den Gruppendateien. Mit `-r` löscht es zusätzlich Heimatverzeichnis und Mail-Postfach. Es ist das Basiswerkzeug der Shadow-Suite; unter Debian und Ubuntu empfiehlt die [Debian-Manpage zu userdel](https://manpages.debian.org/trixie/passwd/userdel.8.en.html) für die normale Verwaltung `deluser`.

**Root-Rechte sind immer nötig.**

## 2. Was macht der Befehl?

`userdel KONTO`:

- entfernt alle Kontoeinträge und die Mitgliedschaften in Gruppen,
- löscht bei `USERGROUPS_ENAB yes` (auf dem geprüften System gesetzt) die **gleichnamige persönliche Gruppe**, sofern sie nicht primäre Gruppe eines anderen Kontos ist,
- verweigert die Löschung, solange **Prozesse des Kontos laufen** (Rückgabewert 8),
- lässt **Heimatverzeichnis und alle Dateien** unangetastet, wenn `-r` fehlt.

Mit `-r` werden das Heimatverzeichnis und das Postfach unter `MAIL_DIR` (hier `/var/mail`) gelöscht. Dateien an anderen Orten bleiben laut Manpage liegen und müssen manuell gesucht werden.

### userdel und deluser

| Aspekt | `userdel` | `deluser` (Debian) |
| --- | --- | --- |
| Heimatverzeichnis löschen | `-r` | `--remove-home` |
| Alle Dateien im System löschen | nicht vorhanden | `--remove-all-files` |
| Sicherung vor dem Löschen | nicht vorhanden | `--backup`, `--backup-to` |
| Crontab entfernen | nein | ja |

## 3. Syntax

```text
userdel [OPTIONEN] KONTO
```

```bash
sudo userdel anna
sudo userdel -r anna
```

Das bisherige NetMon-Beispiel `userdel --help` zeigt nur die Hilfe; der Platzhalter `userdel [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-r`, `--remove` | Heimatverzeichnis und Mail-Postfach löschen. | Unwiderruflich ohne Sicherung. |
| `-f`, `--force` | Sicherheitsprüfungen überspringen. | Löscht auch bei angemeldetem Konto und ggf. Dateien, die nicht dem Konto gehören. Laut Manpage gefährlich. |
| `-R VERZ`, `--root VERZ` | In anderem Wurzelverzeichnis arbeiten. | Nur absolute Pfade. |
| `-P VERZ`, `--prefix VERZ` | Dateien unter Präfix bearbeiten. | Ohne chroot. |
| `-Z`, `--selinux-user` | SELinux-Zuordnung entfernen. | Nur mit SELinux. |
| `--extrausers` | Zusätzliche Benutzerdatenbank. | Ubuntu-spezifisch. |
| `-h`, `--help` | Hilfe. | – |

**Warnung zu `-f -r`:** Die lokale Hilfe sagt ausdrücklich, dass `-f` auch Dateien entfernt, „even if not owned by the user“. Ohne `-f` lässt `userdel -r` ein Heimatverzeichnis, das nicht dem Konto gehört, stehen (Meldung `... not owned by ..., not removing`). Ist das Heimatverzeichnis falsch eingetragen (etwa ein gemeinsamer Ordner), kann `userdel -f -r` deshalb fremde Daten löschen.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Das Konto `ehemalig` entfernen und das Heimatverzeichnis vorher sichern. Das löscht Daten; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Konto und Heimatverzeichnis prüfen

```bash
getent passwd ehemalig
```

Die sechste Spalte ist das Heimatverzeichnis. Prüfe, dass es wirklich ein eigener Ordner wie `/home/ehemalig` ist.

### Schritt 2: Laufende Prozesse beenden

```bash
ps -u ehemalig
sudo passwd -l ehemalig
```

Ohne laufende Prozesse kann `userdel` ohne `-f` arbeiten. Das Sperren verhindert neue Anmeldungen bis zur Löschung.

### Schritt 3: Sichern

```bash
sudo tar -C /home -czf /root/ehemalig-home.tar.gz ehemalig
```

### Schritt 4: Löschen

```bash
sudo userdel -r ehemalig
echo $?
```

Rückgabewert `0` bedeutet Erfolg. Hinweise wie „mail spool not found“ sind keine Fehler.

### Schritt 5: Reste suchen

```bash
sudo find / -xdev -nouser -print 2>/dev/null | head
sudo crontab -u ehemalig -l
```

`-nouser` findet Dateien, deren UID keinem Konto mehr zugeordnet ist. Ein verbliebener Crontab muss separat entfernt werden.

## 6. Typische Anwendungsfälle

- **Konto nach Austritt entfernen,** nachdem Daten übergeben wurden.
- **Dienstkonto nach Deinstallation** entfernen (oft erledigt das der Paketverwalter).
- **Skripte auf Distributionen ohne `deluser`.**

## 7. Risiken, Nebenwirkungen und Vorsicht

- **Datenverlust mit `-r`:** Heimatverzeichnis und Postfach sind ohne Sicherung verloren.
- **Verwaiste Dateien ohne `-r` oder außerhalb des Heimatordners:** Sie behalten die alte UID. Ein später angelegtes Konto mit derselben UID erhält Zugriff – Datenoffenlegung.
- **`-f`:** Löscht trotz laufender Prozesse und überspringt Prüfungen. Prozesse laufen danach unter einer UID ohne Namen weiter.
- **Persönliche Gruppe:** Wird automatisch mitgelöscht; Dateien dieser Gruppe behalten die GID.
- **Gemeinsame Ordner als Heimatverzeichnis:** Mit `-r` gefährlich.
- **Keine Rückfrage:** Ein Tippfehler im Kontonamen trifft ein anderes Konto.

Die ursprüngliche Einstufung „Rot – destruktiv/möglich kritisch“ bleibt bestehen. Die Root-Angabe „Häufig“ wurde auf „erforderlich“ präzisiert.

## 8. Häufige Fehler

| Meldung oder Rückgabewert | Bedeutung | Vorgehen |
| --- | --- | --- |
| `userdel: user '...' does not exist` (6) | Konto unbekannt. | `getent passwd` prüfen. |
| `userdel: user ... is currently used by process ...` (8) | Prozesse laufen. | Prozesse beenden, Konto sperren, später löschen. |
| Rückgabewert `12` | Heimatverzeichnis konnte nicht gelöscht werden. | Pfad und Einhängepunkte prüfen. |
| `userdel: group ... is the primary group of another user and is not removed.` | Persönliche Gruppe ist primäre Gruppe eines anderen Kontos. | Gruppe bleibt; bewusst prüfen. |
| `userdel: ... not owned by ..., not removing` | Heimatverzeichnis gehört nicht dem Konto. | Pfad prüfen; nicht reflexartig `-f` ergänzen. |
| `userdel: Permission denied.` | Ohne Root. | Mit Verwaltungsrechten. |

Rückgabewerte laut Debian-Manpage; Meldungstexte mit dem lokalen Programm abgeglichen, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Unter Debian/Ubuntu `deluser --backup-to`** verwenden.
2. **Erst sperren, dann löschen** (`passwd -l`, `usermod --expiredate 1`).
3. **Heimatverzeichnis prüfen und sichern,** bevor `-r` verwendet wird.
4. **Kein `-f`** ohne zwingenden Grund.
5. **Danach `find -nouser`** ausführen.

### Prüfstand

- **Geprüfte Version:** shadow 4.13 (Ubuntu-Paket `passwd`); Debian-Manpage shadow 4.17.4.
- **Tatsächlich ausgeführt:** `userdel --help`, Lesen von `MAIL_DIR` und `USERGROUPS_ENAB`, Abgleich der Meldungstexte im Programm.
- **Nicht ausgeführt:** jede Kontolöschung, also Beispiel, Optionen und Fehlerfälle.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `deluser` | Debian-Werkzeug mit Sicherung und Crontab-Entfernung. |
| `useradd`, `usermod` | Konten anlegen und ändern. |
| `passwd -l`, `usermod -L` | Konto sperren statt löschen. |
| `find -nouser`, `find -uid` | Verbliebene Dateien finden. |
| `ps -u`, `pkill -u` | Prozesse eines Kontos anzeigen bzw. beenden. |

Ausgangseintrag: Datensatz 124 in `index.json` (`userdel`, Risiko „Rot – destruktiv/möglich kritisch“, Root „Häufig“). Der Hilfe-Platzhalter wurde durch die tatsächliche Wirkung, Grenzen von `-r`, Gefahren von `-f`, Rückgabewerte und einen vorsichtigen Ablauf ersetzt.
