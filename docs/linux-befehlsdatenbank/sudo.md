---
id: "sudo"
name: "sudo"
command: "sudo"
category: "Benutzer & Rechte"
language: "de"
root_required: false
risk_level: "danger"
tags: ["benutzer", "rechte", "root", "verwaltung"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 120
reviewed_at: "2026-11-13"
locally_checked_version: "sudo 1.9.15p5 (Paket sudo 1.9.15p5-3ubuntu5.24.04.4); nur Hilfe und Version"
---

# sudo – Einzelne Befehle mit Root- oder fremden Rechten ausführen

## 1. Kurzbeschreibung

`sudo` führt einen Befehl als anderes Konto aus, in der Regel als **root**. Anders als `su` fragt es nach **deinem eigenen Passwort** und prüft anhand von Regeln (der „sudoers“-Richtlinie), ob du diesen Befehl ausführen darfst. Jeder Aufruf wird protokolliert.

**Root-Rechte brauchst du zum Aufruf nicht** – `sudo` ist gerade der Weg, sie zu erhalten. Du brauchst aber eine Freigabe in der sudoers-Richtlinie. Unter Ubuntu und davon abgeleiteten Systemen haben Mitglieder der Gruppe `sudo` üblicherweise volle Freigabe. **Prüfpunkt:** Die tatsächlichen Regeln stehen in `/etc/sudoers` und `/etc/sudoers.d/`; sie sind nur für Root lesbar und wurden nicht eingesehen. Was du selbst darfst, zeigt `sudo -l`.

## 2. Was macht der Befehl?

Bei `sudo BEFEHL` passiert Folgendes:

1. `sudo` prüft die Richtlinie: Darf dein Konto diesen Befehl auf diesem Rechner als Zielkonto ausführen?
2. Falls nötig, fragt es **dein** Passwort ab. Nach erfolgreicher Eingabe merkt es sich das für eine gewisse Zeit pro Terminal (Zeitstempel), sodass Folgebefehle ohne erneute Abfrage laufen.
3. Es setzt eine bereinigte Umgebung und startet den Befehl mit den Rechten des Zielkontos.
4. Der Rückgabewert ist der des ausgeführten Befehls. Bei abgelehnter Anmeldung, Richtlinien- oder Ausführungsfehlern liefert `sudo` selbst `1`.

Die Beschreibung folgt der [Debian-Manpage zu sudo](https://manpages.debian.org/trixie/sudo/sudo.8.en.html) (Version 1.9.16p2) und der lokalen Hilfe von sudo 1.9.15p5.

**Hinweis zu Implementierungen:** Einige Distributionen bieten zusätzlich oder statt des klassischen sudo die Neuentwicklung `sudo-rs`. Auf dem geprüften System ist das klassische sudo installiert.

## 3. Syntax

```text
sudo [OPTIONEN] BEFEHL [ARGUMENTE ...]
sudo -u KONTO BEFEHL
sudo -i | -s
sudo -l | -v | -k | -K
```

```bash
sudo apt update
sudo -u postgres psql
sudo -l
sudo -i
```

Das bisherige NetMon-Beispiel `sudo --help` zeigt nur die Hilfe; der Platzhalter `sudo [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-u KONTO` | Als anderes Konto statt root ausführen. | Zum Beispiel für Dienstkonten. |
| `-g GRUPPE` | Mit anderer primärer Gruppe ausführen. | Nur wenn die Richtlinie es erlaubt. |
| `-i`, `--login` | Anmelde-Shell des Zielkontos; liest dessen Startdateien. | Interaktive Root-Sitzung; danach `exit`. |
| `-s`, `--shell` | Shell aus `SHELL` bzw. des Kontos starten. | Umgebung bleibt eher erhalten als bei `-i`. |
| `-l`, `--list` | Eigene Freigaben anzeigen oder einen Befehl prüfen. | `-ll` für ausführliche Form. |
| `-v`, `--validate` | Zeitstempel erneuern, ohne Befehl. | Fragt ggf. nach dem Passwort. |
| `-k`, `--reset-timestamp` | Gemerkte Anmeldung verwerfen. | Mit Befehl: einmalig ohne Zeitstempel ausführen. |
| `-K`, `--remove-timestamp` | Alle gemerkten Anmeldungen löschen. | Ohne Passwort; nicht mit Befehl kombinierbar. |
| `-n`, `--non-interactive` | Nie nachfragen; bei nötigem Passwort Fehler. | Für Skripte. |
| `-e`, `--edit` | Dateien sicher bearbeiten. | Gleich wie `sudoedit`. |
| `-E`, `--preserve-env` | Eigene Umgebung behalten. | Nur wenn erlaubt; Sicherheitsrisiko. |
| `-D VERZ`, `--chdir=VERZ` | Arbeitsordner vor dem Start wechseln. | Nur wenn erlaubt. |
| `-b`, `--background` | Befehl im Hintergrund ausführen. | Keine Rückfragen möglich. |
| `-T SEK`, `--command-timeout=SEK` | Befehl nach Zeitlimit beenden. | Nur wenn die Richtlinie es erlaubt. |
| `-S`, `--stdin` | Passwort von der Standardeingabe lesen. | Passwort landet leicht in Verlauf oder Skripten. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Prüfen, welche Rechte du hast, und dann einen einzelnen Befehl mit Root-Rechten ausführen. Weil das Root-Rechte nutzt, ist es ein **Beispielszenario** und wurde für dieses Dokument nicht ausgeführt.

### Schritt 1: Eigene Freigaben ansehen

```bash
sudo -l
```

Nach der Passworteingabe zeigt `sudo` die für dich geltenden Regeln, zum Beispiel `(ALL : ALL) ALL` – „darf jeden Befehl als jedes Konto ausführen“.

### Schritt 2: Lesenden Befehl mit Root-Rechten

```bash
sudo ls -l /root
```

`/root` ist für normale Benutzer nicht lesbar. Mit `sudo` erscheint der Inhalt. Der Befehl verändert nichts.

### Schritt 3: Wer bin ich?

```bash
sudo id -un
id -un
```

Die erste Zeile gibt `root` aus, die zweite deinen Kontonamen: `sudo` wirkt nur für den einen Befehl.

### Schritt 4: Gemerkte Anmeldung beenden

```bash
sudo -k
```

Danach fragt der nächste `sudo`-Aufruf wieder nach dem Passwort. Das ist sinnvoll, bevor du den Rechner unbeaufsichtigt lässt.

## 6. Typische Anwendungsfälle

| Aufgabe | Aufruf |
| --- | --- |
| Paketverwaltung | `sudo apt install PAKET` |
| Systemdatei bearbeiten | `sudoedit /etc/hosts` |
| Dienst neu starten | `sudo systemctl restart DIENST` |
| Befehl als Dienstkonto | `sudo -u www-data php skript.php` |
| Kurze Root-Sitzung | `sudo -i`, danach `exit` |

## 7. Risiken, Nebenwirkungen und Vorsicht

### Warum „danger“

`sudo` führt Befehle mit vollen Systemrechten aus. Jeder Tippfehler, jedes falsch kopierte Kommando und jedes fehlerhafte Skript wirkt dann auf das ganze System – bis zum Löschen von Systemdateien oder dem Aussperren aller Benutzer. Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ wurde deshalb auf `danger` angehoben. Das Risiko eines Aufrufs entspricht dem Risiko des ausgeführten Befehls mit Root-Rechten.

### Hinweise aus der Manpage

- **Shells und Shell-Ausbrüche:** Nach `sudo su` oder `sudo sh` unterliegen weitere Befehle nicht mehr der Richtlinie und werden nicht einzeln protokolliert. Viele Programme (Editoren, `less`, Interpreter) erlauben Shell-Ausbrüche. Eine Freigabe für solche Programme ist praktisch eine Freigabe für alles.
- **Beschreibbare Programme:** Eine Freigabe für Dateien, die der Benutzer selbst ändern kann oder die in einem für ihn beschreibbaren Ordner liegen, lässt sich nicht begrenzen.
- **Umgebung:** `-E` übernimmt deine Variablen, etwa `PATH` oder `LD_PRELOAD`-ähnliche Einflüsse, sofern erlaubt. Das kann Root-Prozesse beeinflussen.

### Praktische Gefahren

- **`sudo` vor einer Umleitung wirkt nicht wie erwartet:** Bei `sudo echo text > /etc/datei` öffnet deine eigene Shell die Datei, nicht `sudo`. Richtig: `echo text | sudo tee /etc/datei` – und auch das nur bewusst, weil `tee` überschreibt.
- **Dateien im Heimatordner:** Programme, die mit `sudo` gestartet werden, können Dateien in deinem Heimatordner als Root anlegen. Danach fehlen dir Schreibrechte.
- **Kopierte Befehle aus dem Internet** nicht ungeprüft mit `sudo` ausführen.
- **Zeitstempel:** Während der gemerkten Zeit können auch Skripte im selben Terminal ohne Passwort `sudo` nutzen. **Prüfpunkt:** Die Dauer legt die Richtlinie fest (`timestamp_timeout`).

## 8. Häufige Fehler

| Meldung | Ursache | Vorgehen |
| --- | --- | --- |
| `... is not in the sudoers file.` | Keine Freigabe für dein Konto. | Verwaltung fragen; der Versuch wird protokolliert. |
| `Sorry, user ... is not allowed to execute '...' as root on ...` | Freigabe deckt diesen Befehl nicht ab. | Mit `sudo -l` die erlaubten Befehle ansehen. |
| `Sorry, try again.` | Falsches Passwort. | Erneut eingeben; nach mehreren Fehlversuchen Abbruch. |
| `a password is required` | `-n` verwendet, aber Passwort nötig. | Ohne `-n` interaktiv ausführen. |
| `sudo: BEFEHL: command not found` | Befehl nicht im sicheren `PATH` von sudo. | Vollständigen Pfad angeben. |
| `Permission denied` trotz sudo bei `>` | Umleitung läuft ohne Root-Rechte. | `sudo tee` verwenden. |

Die englischen Meldungstexte wurden im lokalen sudoers-Plugin (`/usr/libexec/sudo/sudoers.so`) abgeglichen, aber nicht praktisch ausgelöst. Mit deutscher Spracheinstellung erscheinen Übersetzungen.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Nur einzelne Befehle mit `sudo`,** keine dauerhaften Root-Shells.
2. **Befehl vor dem Absenden noch einmal lesen,** besonders Pfade und Sternchen.
3. **Dateien mit `sudoedit`** statt `sudo nano` oder `sudo vim` bearbeiten.
4. **`sudo -k`** vor Pausen ausführen.
5. **`sudo -l`** zeigt, was überhaupt erlaubt ist.
6. **sudoers nur mit `visudo`** bearbeiten.

### Prüfstand

- **Geprüfte Version:** sudo 1.9.15p5 (Ubuntu-Paket); Debian-Manpage 1.9.16p2.
- **Tatsächlich ausgeführt:** `sudo -h` und `sudo -V`. Der Inhalt von `/etc/sudoers` war für das Konto nicht lesbar.
- **Nicht ausgeführt:** jeder Aufruf mit Rechtewechsel (`sudo -l`, `sudo BEFEHL`, `-i`, `-k`, `-K`), weil diese Root-Rechte nutzen oder den Anmeldezustand des Benutzers verändern. Alle Fehlermeldungen und Rückgabewerte stammen aus der Dokumentation.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `sudoedit` | Bearbeitet Dateien sicher mit Root-Rechten. |
| `visudo` | Bearbeitet und prüft die sudoers-Richtlinie. |
| `su` | Wechselt mit dem Passwort des Zielkontos. |
| `pkexec` | Führt Programme über polkit mit erhöhten Rechten aus. |
| `runuser` | Kontowechsel für Root-Skripte ohne Passwort. |
| `id`, `whoami` | Zeigen das aktuelle Konto. |

Ausgangseintrag: Datensatz 120 in `index.json` (`sudo`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch den Ablauf der Rechteprüfung, Optionen, Sicherheitsnotizen der Manpage und typische Fallen ersetzt. Die Risikostufe wurde auf „Gefahr“ angehoben, weil `sudo` Befehle mit vollen Systemrechten ausführt.
