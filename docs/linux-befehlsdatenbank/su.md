---
id: "su"
name: "su"
command: "su"
category: "Benutzer & Rechte"
language: "de"
root_required: false
risk_level: "caution"
tags: ["benutzer", "rechte", "benutzerwechsel", "root"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 119
reviewed_at: "2026-11-13"
locally_checked_version: "util-linux 2.39.3; nur Hilfe, Version und PAM-Konfiguration"
---

# su – Als anderer Benutzer arbeiten

## 1. Kurzbeschreibung

`su` („substitute user“) startet eine Shell oder einen Befehl unter einem anderen Benutzerkonto. Ohne Kontoname ist das Ziel **root**. Anders als `sudo` verlangt `su` das **Passwort des Zielkontos**, nicht dein eigenes.

**Root-Rechte sind zum Aufrufen nicht nötig.** `su` ist ein SUID-Programm. Du brauchst aber das Passwort des Zielkontos. Root kann ohne Passwort zu jedem Konto wechseln.

**Hinweis für Ubuntu und davon abgeleitete Systeme:** Das Root-Konto hat dort standardmäßig kein nutzbares Passwort. `su` ohne Kontoname scheitert dann mit einem Authentifizierungsfehler. Für Root-Arbeit ist auf diesen Systemen `sudo` vorgesehen.

## 2. Was macht der Befehl?

`su` prüft über **PAM** das Passwort, wechselt Benutzer- und Gruppen-IDs und startet die Shell des Zielkontos. Was mit der Umgebung passiert, hängt entscheidend von `-` beziehungsweise `--login` ab:

| Aufruf | Arbeitsordner | Umgebung |
| --- | --- | --- |
| `su anna` | bleibt | Nur `HOME`, `SHELL` (bei Nicht-Root auch `USER`, `LOGNAME`) werden gesetzt; der Rest bleibt von dir. |
| `su - anna` oder `su --login anna` | Heimatordner von `anna` | Umgebung wird gelöscht und wie bei einer Anmeldung neu aufgebaut, inklusive `PATH`. |

Laut [Debian-Manpage zu su](https://manpages.debian.org/trixie/util-linux/su.1.en.html) wird ausdrücklich empfohlen, **immer `--login`** zu verwenden, um Nebenwirkungen durch vermischte Umgebungen zu vermeiden. Die Manpage betont außerdem: `su` ist für normale Benutzer gedacht; Root-Skripte sollten `runuser` oder `setpriv` verwenden.

Diese Beschreibung gilt für `su` aus **util-linux**, wie es Debian, Ubuntu und viele andere Distributionen ausliefern. Ältere oder andere Fassungen (etwa aus der Shadow-Suite oder BusyBox) unterscheiden sich in Details.

## 3. Syntax

```text
su [OPTIONEN] [-] [KONTO [ARGUMENTE ...]]
```

```bash
su - anna
su - anna -c 'id; pwd'
su -
```

Das bisherige NetMon-Beispiel `su --help` zeigt nur die Hilfe; der Platzhalter `su [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-`, `-l`, `--login` | Anmelde-Shell mit frischer Umgebung. | Empfohlene Standardwahl. |
| `-c BEFEHL`, `--command BEFEHL` | Nur einen Befehl ausführen. | Befehl in Anführungszeichen setzen. |
| `-s SHELL`, `--shell SHELL` | Andere Shell verwenden. | Bei Zielkonten mit eingeschränkter Shell nur für Root. |
| `-m`, `-p`, `--preserve-environment` | Umgebung vollständig behalten. | Wird mit `--login` ignoriert; Risiko vermischter Umgebungen. |
| `-w LISTE`, `--whitelist-environment LISTE` | Bestimmte Variablen bei `--login` behalten. | `HOME`, `SHELL`, `USER`, `LOGNAME`, `PATH` werden trotzdem neu gesetzt. |
| `-P`, `--pty` | Eigenes Pseudo-Terminal anlegen. | Schützt vor Terminal-Einschleusung; siehe Abschnitt 7. |
| `-g GRUPPE`, `-G GRUPPE` | Primäre oder zusätzliche Gruppe setzen. | Nur für Root. |
| `-f`, `--fast` | `-f` an die Shell weitergeben. | Für csh/tcsh. |
| `-h`, `--help`, `-V`, `--version` | Hilfe, Version. | – |

**Versionshinweis:** Die Debian-Manpage (util-linux 2.41.5) beschreibt zusätzlich `-T`/`--no-pty`. Die lokal geprüfte Fassung 2.39.3 nennt diese Option in ihrer Hilfe nicht. **Prüfpunkt:** Verfügbarkeit mit `su --help` prüfen.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Als Konto `anna` einen Befehl ausführen und prüfen, mit welchen Rechten er läuft. Voraussetzung: Du kennst das Passwort von `anna`. Das Beispiel wurde **nicht ausgeführt**, weil dafür ein zweites Konto mit bekanntem Passwort nötig wäre.

### Schritt 1: Einzelnen Befehl als anderes Konto

```bash
su - anna -c 'id; pwd'
```

`su` fragt nach dem Passwort von `anna`. Danach zeigt `id` die Kennung und Gruppen von `anna`, `pwd` deren Heimatordner – weil `-` eine Anmeldeumgebung erzeugt.

### Schritt 2: Unterschied ohne Bindestrich

```bash
su anna -c 'pwd; echo $PATH'
```

Jetzt bleibt der Arbeitsordner dein bisheriger, und `PATH` ist deiner. Genau diese Mischung empfiehlt die Manpage zu vermeiden.

### Schritt 3: Interaktive Sitzung beenden

Nach `su - anna` ohne `-c` arbeitest du in einer Shell als `anna`. Mit `exit` kehrst du zu deiner eigenen Shell zurück. Prüfe mit `whoami`, wer du gerade bist.

### Rückgabewert

`su` gibt laut Manpage den Rückgabewert des ausgeführten Befehls zurück. Eigene Fehler: `1` (vor der Ausführung, etwa falsches Passwort), `126` (Befehl nicht ausführbar), `127` (Befehl nicht gefunden).

## 6. Typische Anwendungsfälle

- **Fehlersuche aus Sicht eines anderen Kontos:** Zugriffe testen, wie sie `anna` erlebt.
- **Root-Shell auf Systemen mit Root-Passwort** (etwa Debian ohne sudo): `su -`.
- **Als Root in ein Dienstkonto wechseln:** `sudo su - postgres -s /bin/bash` oder besser `sudo -u postgres -i`. Für Skripte empfiehlt die Manpage `runuser`.

## 7. Risiken, Nebenwirkungen und Vorsicht

- **Root-Shell:** Nach `su -` läuft jeder Befehl mit vollen Rechten. Tippfehler wirken systemweit. Die Shell möglichst kurz offen halten.
- **Umgebung ohne `-`:** Deine Variablen wie `PATH` oder `LD_LIBRARY_PATH` gelten im Zielkonto weiter. Als Root kann das unbeabsichtigt Programme aus deinen Ordnern starten.
- **Terminal-Einschleusung:** Ohne eigenes Pseudo-Terminal teilen sich beide Konten ein Terminal. Die Manpage warnt vor Rechteausweitung über TIOCSTI/TIOCLINUX-Einschleusung; `--pty` schützt davor, insbesondere wenn Root mit `su` in ein weniger vertrauenswürdiges Konto wechselt.
- **Passwortweitergabe:** Damit mehrere Personen `su` zu Root nutzen können, müssen sie das Root-Passwort kennen. `sudo` mit persönlichen Passwörtern und Protokollierung ist nachvollziehbarer.
- **Keine vollständige Sitzung:** Laut Manpage erzeugt `su` keine echte systemd-Sitzung; Benutzerdienste des Zielkontos stehen dann nicht unbedingt zur Verfügung.
- **Protokollierung:** Erfolgreiche und fehlgeschlagene Versuche werden im Systemprotokoll vermerkt. Wiederholte Fehlversuche können Sicherheitsmeldungen auslösen.

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt bestehen.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `su: Authentication failure` | Falsches Passwort oder Root-Passwort gesperrt (Ubuntu). | Für Root `sudo -i` verwenden. |
| `su: user ... does not exist or the user entry does not contain all the required fields` | Konto unbekannt. | `getent passwd NAME` prüfen. |
| Befehl nicht gefunden nach `su` ohne `-` | Falscher `PATH`. | `su -` verwenden. |
| `This account is currently not available.` | Zielkonto hat `nologin` als Shell. | Als Root mit `-s /bin/bash` oder `runuser`. |

Die Meldung zum unbekannten Konto ist im lokalen `su` enthalten, die zu `nologin` in `/usr/sbin/nologin`. **Prüfpunkt:** `Authentication failure` stammt aus PAM; keiner der Texte wurde praktisch ausgelöst, und alle hängen von Version, PAM und Spracheinstellung ab.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Immer `su -`** statt `su` ohne Bindestrich.
2. **Für einzelne Befehle `-c`** verwenden und danach automatisch zurückkehren.
3. **Auf Ubuntu-artigen Systemen `sudo`** statt `su` für Root-Aufgaben.
4. **Root-Shells sofort mit `exit` beenden.**
5. **`whoami` prüfen,** bevor du kritische Befehle ausführst.
6. **Root-Skripte mit `runuser` oder `setpriv`** statt `su`.

### Prüfstand

- **Geprüfte Version:** su aus util-linux 2.39.3.
- **Tatsächlich ausgeführt:** `su --help`, `su --version`, Lesen von `/etc/pam.d/su` (kein `pam_wheel` aktiv, `pam_rootok` für Root).
- **Nicht ausgeführt:** jeder tatsächliche Kontowechsel, also Beispiel, Umgebungsunterschiede, `--pty` und alle Fehlermeldungen. Dafür wären Passwörter anderer Konten nötig gewesen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `sudo` | Führt Befehle nach Regeln mit dem eigenen Passwort aus; protokolliert genauer. |
| `sudo -i`, `sudo -u KONTO -i` | Anmelde-Shell als Root beziehungsweise anderes Konto. |
| `runuser` | Kontowechsel für Root ohne Passwortabfrage; für Skripte. |
| `setpriv` | Setzt IDs und Rechte ohne PAM-Sitzung. |
| `newgrp`, `sg` | Wechseln nur die Gruppe. |
| `whoami`, `id` | Zeigen, unter welchem Konto du arbeitest. |

Ausgangseintrag: Datensatz 119 in `index.json` (`su`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch die Unterscheidung mit und ohne `--login`, die Passwortlogik, die Ubuntu-Besonderheit, Rückgabewerte und Sicherheitshinweise ersetzt.
