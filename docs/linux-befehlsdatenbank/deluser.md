---
id: "deluser"
name: "deluser"
command: "deluser"
category: "Benutzer & Rechte"
language: "de"
root_required: true
risk_level: "danger"
tags: ["benutzer", "konten", "kontenverwaltung", "debian"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 107
reviewed_at: "2026-11-13"
locally_checked_version: "adduser 3.137ubuntu1; nur Hilfe, Version, Nicht-Root-Ablehnung und Quelltext"
---

# deluser – Benutzerkonto entfernen oder Benutzer aus einer Gruppe nehmen (Debian-Werkzeug)

## 1. Kurzbeschreibung

`deluser` ist das komfortable Debian- und Ubuntu-Werkzeug zum Entfernen von Benutzerkonten. Es gehört zum Paket **adduser**, ist in Perl geschrieben und ruft intern `userdel` beziehungsweise `groupdel` auf. Zusätzlich kann es das Heimatverzeichnis oder alle Dateien des Kontos löschen und vorher sichern.

**Root-Rechte sind immer nötig.** Ohne Root bricht `deluser` mit `fatal: Only root may remove a user or group from the system.` und Rückgabewert `54` ab.

## 2. Was macht der Befehl?

`deluser` kennt drei Modi, die sich nur an der Zahl der Argumente unterscheiden:

| Aufruf | Wirkung |
| --- | --- |
| `deluser BENUTZER` | Konto entfernen. |
| `deluser BENUTZER GRUPPE` | Nur die Gruppenmitgliedschaft entfernen; Konto bleibt. |
| `deluser --group GRUPPE` | Gruppe entfernen, wie `delgroup`. |

**Ein Tippfehler bei der Argumentzahl ändert den Modus.** Wer `deluser anna sudo` meint und `deluser anna` schreibt, entfernt das ganze Konto statt nur die sudo-Mitgliedschaft.

### Was beim Entfernen eines Kontos passiert

Nach dem lokalen Quelltext von adduser 3.137ubuntu1 und der [Debian-Manpage zu deluser](https://manpages.debian.org/trixie/adduser/deluser.8.en.html):

1. Prüfen, ob das Konto existiert; das Konto `root` (UID 0) wird verweigert.
2. Nur mit `--remove-home` oder `--remove-all-files`: Dateien sammeln, optional mit `--backup` als TAR-Archiv sichern, dann löschen.
3. Einen vorhandenen Crontab des Kontos entfernen (wenn `crontab` installiert ist).
4. `userdel` aufrufen; damit verschwinden die Einträge in `/etc/passwd`, `/etc/shadow` und die Gruppenmitgliedschaften.
5. Optional das lokale Zusatzskript `/usr/local/sbin/deluser.local` ausführen.

**Standardmäßig bleiben Heimatverzeichnis, Mail-Postfach und alle anderen Dateien erhalten.** Sie gehören danach einer nicht mehr zugeordneten UID.

### Andere Systeme

`deluser` mit diesen Optionen gibt es nur in der Debian-Familie. Andere Distributionen verwenden `userdel`. BusyBox hat ein stark vereinfachtes `deluser BENUTZER` ([BusyBox-Befehlsübersicht](https://busybox.net/downloads/BusyBox.html)).

## 3. Syntax

```text
deluser [--remove-home] [--remove-all-files] [--backup] [--backup-to VERZ] BENUTZER
deluser --system [OPTIONEN] BENUTZER
deluser BENUTZER GRUPPE
deluser --group [--only-if-empty] GRUPPE
```

```bash
sudo deluser anna docker
sudo deluser --backup-to /root/konten-archiv --remove-home ehemalig
```

Das bisherige NetMon-Beispiel `deluser --help` zeigt nur die Hilfe; der Platzhalter `deluser [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--remove-home` | Heimatverzeichnis und Mail-Postfach löschen. | Unwiderruflich ohne Sicherung. |
| `--remove-all-files` | Alle Dateien des Kontos im ganzen System löschen. | Durchsucht `/`; kann lange dauern; schließt `--remove-home` ein. |
| `--backup` | Zu löschende Dateien vorher als `BENUTZER.tar.gz` sichern. | Nur wirksam zusammen mit einer Löschoption. |
| `--backup-to VERZ` | Sicherungsordner wählen; setzt `--backup`. | Ohne Angabe: aktuelles Arbeitsverzeichnis. |
| `--backup-suffix ENDUNG` | Kompression der Sicherung, z. B. `.xz`. | Muss von `tar --auto-compress` erkannt werden. |
| `--system` | Nur löschen, wenn es ein Systemkonto ist. | Fehlt das Konto, Rückgabe `0`. |
| `--group` | Gruppe statt Konto entfernen. | Entspricht `delgroup`. |
| `--only-if-empty` | Gruppe nur löschen, wenn sie leer ist. | Nur im Gruppenmodus. |
| `--conf DATEI` | Andere Konfiguration statt `/etc/deluser.conf`. | Siehe Sicherheitshinweis in Abschnitt 7. |

### Schutz durch NO_DEL_PATHS

Bei `--remove-all-files` überspringt `deluser` Pfade, die auf die regulären Ausdrücke in `NO_DEL_PATHS` passen, und Einhängepunkte bestimmter Dateisystemtypen (`EXCLUDE_FSTYPES`). Die Vorgaben stehen in `/etc/deluser.conf`; dort ist auf dem geprüften System alles auskommentiert, es gelten also die eingebauten Standardwerte. **Prüfpunkt:** Diese Schutzliste ersetzt keine Durchsicht der betroffenen Dateien.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Das Konto `ehemalig` entfernen und sein Heimatverzeichnis vorher sichern. Das verändert Konten und löscht Daten; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Konto und Prozesse prüfen

```bash
getent passwd ehemalig
ps -u ehemalig
```

Der erste Befehl zeigt Kontodaten und Heimatverzeichnis. Laufen noch Prozesse des Kontos, verweigert `userdel` die Löschung meist. Prozesse vorher kontrolliert beenden lassen.

### Schritt 2: Sicherungsordner vorbereiten

```bash
sudo install -d -m 700 /root/konten-archiv
df -h /root/konten-archiv
```

Der Ordner ist nur für Root lesbar. `df` zeigt, ob genug Platz für die Sicherung vorhanden ist.

### Schritt 3: Konto mit Sicherung entfernen

```bash
sudo deluser --backup-to /root/konten-archiv --remove-home ehemalig
```

`deluser` sammelt die Dateien des Heimatverzeichnisses und das Mail-Postfach, packt sie nach `/root/konten-archiv/ehemalig.tar.gz` (Rechte `0600`, Eigentümer Root), löscht sie, entfernt den Crontab und dann das Konto.

### Schritt 4: Ergebnis prüfen

```bash
getent passwd ehemalig; echo $?
sudo tar -tzf /root/konten-archiv/ehemalig.tar.gz | head
```

`getent` liefert keine Ausgabe und Rückgabewert `2`. Die Archivliste zeigt die gesicherten Pfade ohne führenden Schrägstrich.

## 6. Typische Anwendungsfälle

- **Benutzer aus einer Gruppe nehmen:** `sudo deluser anna docker`. Wirksam ab der nächsten Anmeldung von `anna`.
- **Mitarbeiterkonto stilllegen:** Oft ist vorübergehendes Sperren (`usermod -L`, Ablaufdatum) besser als Löschen, bis Daten übergeben sind.
- **Paketdeinstallation:** Paketskripte nutzen `deluser --system DIENST`.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Datenverlust

`--remove-home` und vor allem `--remove-all-files` löschen Dateien endgültig. `--remove-all-files` erfasst auch Dateien in gemeinsamen Ordnern wie `/srv` oder `/var/www`, die dem Konto gehören. Ohne `--backup` gibt es keinen Rückweg außer einer externen Sicherung.

### Verwaiste Dateien ohne Löschoption

Ohne Löschoption bleiben die Dateien mit der alten UID liegen. Erhält ein neues Konto später dieselbe UID, gehören ihm diese Dateien – eine Datenoffenlegung. Nach dem Löschen deshalb mit `find / -xdev -nouser` prüfen.

### Laufende Prozesse und Dienste

Prozesse, Cron-Aufträge, systemd-Benutzerdienste oder Container des Kontos können Fehler verursachen. Den Crontab entfernt `deluser`; andere zeitgesteuerte Aufgaben nicht.

### Sicherheitshinweis zu sudo-Freigaben

Die Manpage warnt: Eine eingeschränkte `sudo`-Freigabe für `deluser` lässt sich leicht umgehen, etwa über `--conf`. Teilrechte nur über ein eigenes, geprüftes Skript vergeben.

### Root-Konto

`deluser` verweigert das Löschen von UID 0. Der lokale Quelltext kennt dafür eine Übersteuerung, die in der Manpage nicht beschrieben ist; sie gehört in keine normale Verwaltung.

Die ursprüngliche Einstufung „Rot – destruktiv/möglich kritisch“ bleibt bestehen. Die Root-Angabe wurde auf „erforderlich“ korrigiert.

## 8. Häufige Fehler

| Meldung oder Rückgabewert | Bedeutung | Vorgehen |
| --- | --- | --- |
| `fatal: Only root may remove a user or group from the system.` (54) | Ohne Root aufgerufen. | Nur mit Verwaltungsrechten. |
| `The user '...' does not exist.` (12) | Konto unbekannt. | Namen mit `getent passwd` prüfen. |
| `The user '...' is not a system user. Exiting.` (13) | `--system` bei normalem Konto. | Absicht prüfen. |
| `The user '...' is not a member of group '...'.` (42) | Mitgliedschaft bestand nicht. | `id BENUTZER` prüfen. |
| `You may not remove the user from their primary group.` (43) | Primäre Gruppe kann nicht entfernt werden. | Primäre Gruppe mit `usermod -g` ändern. |
| `userdel: user ... is currently used by process ...`, danach Rückgabe 82 | Konto hat laufende Prozesse. | Prozesse beenden, Sitzung abmelden lassen. |
| Rückgabewert `55` | Versuch, `root` zu löschen. | Nicht übersteuern. |

Die Rückgabewerte stammen aus der [Debian-Manpage zu adduser](https://manpages.debian.org/trixie/adduser/adduser.8.en.html), die Meldungstexte aus dem lokalen Quelltext. Praktisch ausgelöst wurde nur Wert `54`. Die Meldung `userdel: user ... is currently used by process ...` ist im lokalen `userdel` (shadow 4.13) enthalten. Im Original verwenden die adduser-Meldungen die Anführungszeichenform `` `name' ``.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Argumentzahl doppelt prüfen:** Zwei Namen = Gruppenmitgliedschaft entfernen, ein Name = Konto löschen.
2. **Erst sperren, später löschen,** wenn Daten oder Zuständigkeiten noch zu klären sind.
3. **Immer mit `--backup-to`** arbeiten, wenn eine Löschoption verwendet wird.
4. **Danach verwaiste Dateien suchen:** `sudo find / -xdev -nouser`.
5. **Keine eingeschränkten sudo-Freigaben** für `deluser` erteilen.

### Prüfstand

- **Geprüfte Version:** adduser 3.137ubuntu1 (Ubuntu 24.04-Basis); Debian-Manpage trixie zum Vergleich.
- **Tatsächlich ausgeführt:** `deluser --help`, `deluser --version`, Aufruf als normaler Benutzer (Rückgabe 54), Lesen von `/etc/deluser.conf` und des Perl-Quelltexts (Ablauf, Sicherung, Crontab, Root-Schutz).
- **Nicht ausgeführt:** jede Konto- oder Gruppenänderung, Sicherung, Löschoptionen, `--system` sowie die übrigen Rückgabewerte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `userdel` | Basiswerkzeug der Shadow-Suite; auf allen Distributionen vorhanden. |
| `delgroup` | Verweis auf `deluser` für Gruppen. |
| `adduser`, `useradd` | Legen Konten an. |
| `usermod -L`, `passwd -l` | Sperren ein Konto, ohne es zu löschen. |
| `gpasswd -d` | Entfernt einen Benutzer aus einer Gruppe. |
| `find -nouser` | Findet Dateien ohne zugehöriges Konto. |

Ausgangseintrag: Datensatz 107 in `index.json` (`deluser`, Risiko „Rot – destruktiv/möglich kritisch“, Root „Nein/selten“). Die Root-Angabe wurde auf „erforderlich“ korrigiert. Der Hilfe-Platzhalter wurde durch die drei Modi, den tatsächlichen Ablauf einer Kontolöschung, Sicherungsoptionen, Rückgabewerte und die Falle der Argumentzahl ersetzt.
