---
id: "useradd"
name: "useradd"
command: "useradd"
category: "Benutzer & Rechte"
language: "de"
root_required: true
risk_level: "caution"
tags: ["benutzer", "konten", "kontenverwaltung", "shadow"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 123
reviewed_at: "2026-11-13"
locally_checked_version: "shadow 4.13 (Paket passwd 1:4.13+dfsg1-4ubuntu3.2); nur Hilfe und Vorgaben"
---

# useradd – Neues Benutzerkonto anlegen (Basiswerkzeug)

## 1. Kurzbeschreibung

`useradd` legt ein neues Benutzerkonto an: Eintrag in `/etc/passwd` und `/etc/shadow`, auf Wunsch eine gleichnamige Gruppe und ein Heimatverzeichnis. Es ist das Basiswerkzeug der Shadow-Suite und auf praktisch allen Linux-Distributionen vorhanden.

**Root-Rechte sind nötig.**

Laut [Debian-Manpage zu useradd](https://manpages.debian.org/trixie/passwd/useradd.8.en.html) ist `useradd` ein Werkzeug „niedriger Ebene“; unter Debian sollte die Verwaltung normalerweise `adduser` verwenden. `adduser` fragt interaktiv nach Passwort und Namen und legt ein Heimatverzeichnis an. `useradd` tut nur genau das, was die Optionen verlangen – das macht es für Skripte geeignet, für Einsteiger aber fehleranfällig.

## 2. Was macht der Befehl?

Ohne weitere Optionen erzeugt `useradd anna` auf dem geprüften System:

- einen Eintrag mit der nächsten freien UID ab `UID_MIN` (hier 1000),
- eine gleichnamige Gruppe, weil `USERGROUPS_ENAB yes` gesetzt ist,
- **kein Heimatverzeichnis** (es wird nur in `/etc/passwd` als `/home/anna` eingetragen),
- als Shell `/bin/sh` (laut `useradd -D`),
- **kein nutzbares Passwort**: Das Konto ist für Passwortanmeldungen gesperrt, bis `passwd anna` ausgeführt wird.

Die Vorgaben zeigt `useradd -D`. Auf dem geprüften System:

```text
GROUP=100
HOME=/home
INACTIVE=-1
EXPIRE=
SHELL=/bin/sh
SKEL=/etc/skel
CREATE_MAIL_SPOOL=no
LOG_INIT=yes
```

Weitere Vorgaben stammen aus `/etc/login.defs`, etwa `HOME_MODE 0750` für die Rechte neuer Heimatverzeichnisse. **Prüfpunkt:** Andere Distributionen setzen `CREATE_HOME yes` oder eine andere Shell; das Ergebnis eines nackten `useradd` unterscheidet sich deshalb zwischen Systemen.

## 3. Syntax

```text
useradd [OPTIONEN] KONTONAME
useradd -D [OPTIONEN]
```

```bash
sudo useradd -m -s /bin/bash -c "Anna Beispiel" anna
sudo useradd -r -s /usr/sbin/nologin -d /var/lib/meindienst meindienst
useradd -D
```

Das bisherige NetMon-Beispiel `useradd --help` zeigt nur die Hilfe; der Platzhalter `useradd [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-m`, `--create-home` | Heimatverzeichnis anlegen und Dateien aus `/etc/skel` kopieren. | Unter Debian/Ubuntu meist nötig. |
| `-M`, `--no-create-home` | Kein Heimatverzeichnis anlegen. | Für Dienstkonten. |
| `-s SHELL` | Anmelde-Shell. | Für Personen meist `/bin/bash`; für Dienste `/usr/sbin/nologin`. |
| `-c TEXT` | GECOS-Feld (voller Name). | Wie bei `chfn`. |
| `-d VERZ` | Pfad des Heimatverzeichnisses. | Ohne `-m` wird es nicht angelegt. |
| `-u UID` | Bestimmte UID. | Muss frei sein, außer mit `-o`. |
| `-g GRUPPE` | Primäre Gruppe. | Gruppe muss existieren. |
| `-G G1,G2` | Zusätzliche Gruppen. | Vorsicht bei `sudo`, `docker`, `adm`. |
| `-U` / `-N` | Persönliche Gruppe anlegen bzw. nicht anlegen. | Vorgabe über `USERGROUPS_ENAB`. |
| `-r`, `--system` | Systemkonto (UID aus dem Systembereich). | Kein Heimatverzeichnis, sofern nicht `-m`. |
| `-e DATUM` | Ablaufdatum des Kontos (`JJJJ-MM-TT`). | Für befristete Zugänge. |
| `-p HASH` | Verschlüsseltes Passwort setzen. | Laut Manpage nicht empfohlen: in der Prozessliste sichtbar. |
| `-k VERZ` | Andere Vorlage statt `/etc/skel`. | Nur mit `-m`. |
| `-D` | Vorgaben anzeigen oder ändern. | Anzeigen ohne Root möglich; Ändern verändert Systemvorgaben. |
| `--badname` | Namensprüfung abschalten. | Nur in Ausnahmefällen. |

Die lokale Fassung kennt zusätzlich `--extrausers` (Ubuntu-spezifisch) und `--btrfs-subvolume-home`.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Ein normales Konto `anna` mit Heimatverzeichnis, Bash und Namen anlegen und ihm ein Passwort geben. Das verändert die Kontodatenbank; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Name prüfen

```bash
getent passwd anna
```

Keine Ausgabe heißt: frei.

### Schritt 2: Konto anlegen

```bash
sudo useradd -m -s /bin/bash -c "Anna Beispiel" anna
```

- `-m` legt `/home/anna` an und kopiert die Vorlagen aus `/etc/skel`.
- `-s /bin/bash` setzt die Shell.
- `-c` trägt den Namen ein.

### Schritt 3: Passwort setzen

```bash
sudo passwd anna
```

Ohne diesen Schritt kann sich `anna` nicht mit Passwort anmelden.

### Schritt 4: Kontrolle

```bash
getent passwd anna
id anna
ls -ld /home/anna
```

Erwartet: Eintrag mit `/home/anna` und `/bin/bash`, eine Gruppe `anna`, Heimatverzeichnis mit den Rechten aus `HOME_MODE` (hier `drwxr-x---`).

## 6. Typische Anwendungsfälle

- **Skripte und Automatisierung:** Konten mit festen UIDs und Gruppen reproduzierbar anlegen.
- **Dienstkonten:** `useradd -r -s /usr/sbin/nologin -M dienst`.
- **Befristete Zugänge:** `-e 2026-12-31`.
- **Interaktive Verwaltung unter Debian/Ubuntu:** besser `adduser`.

## 7. Risiken, Nebenwirkungen und Vorsicht

- **Unvollständige Konten:** Ohne `-m` fehlt das Heimatverzeichnis; ohne `-s` gibt es nur `/bin/sh`. Anmeldungen wirken dann „kaputt“.
- **Rechte über Gruppen:** `-G sudo` oder `-G docker` gibt praktisch Root-Rechte.
- **UID-Wiederverwendung:** Eine neue UID, die früher einem gelöschten Konto gehörte, übernimmt dessen verbliebene Dateien. Vorher mit `find / -xdev -uid UID` prüfen.
- **Passwort in der Befehlszeile:** `-p` macht den Hash für andere Prozesse sichtbar; Passwörter mit `passwd` setzen.
- **`-D` mit Optionen** ändert die Systemvorgaben für alle künftigen Konten.
- **Protokolleinträge:** Das Anlegen wird im Systemprotokoll vermerkt (bei `groupadd` beobachtet; für `useradd` ist das gleiche Verhalten zu erwarten, aber nicht geprüft).

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt bestehen. Die Root-Angabe „Häufig“ wurde auf „erforderlich“ präzisiert.

## 8. Häufige Fehler

| Meldung oder Rückgabewert | Bedeutung | Vorgehen |
| --- | --- | --- |
| `useradd: user '...' already exists` (9) | Name vergeben. | Anderen Namen wählen. |
| `useradd: UID ... is not unique` (4) | UID vergeben. | Andere UID oder automatisch vergeben lassen. |
| `useradd: group '...' does not exist` (6) | Gruppe bei `-g` oder `-G` fehlt. | Gruppe zuerst anlegen. |
| `useradd: invalid user name '...': use --badname to ignore` (19 bzw. 3) | Name verstößt gegen Regeln. | Kleinbuchstaben, Ziffern, `_`, `-`. |
| Rückgabewert `12` | Heimatverzeichnis konnte nicht angelegt werden. | Pfad, Platz und Rechte prüfen. |
| `useradd: Permission denied.` | Ohne Root. | Mit Verwaltungsrechten. |
| Anmeldung scheitert | Kein Passwort gesetzt. | `passwd KONTO`. |

Rückgabewerte laut Debian-Manpage. Die englischen Meldungstexte wurden im lokalen Programm abgeglichen, aber nicht praktisch ausgelöst. **Prüfpunkt:** Ob ein ungültiger Name mit 19 oder 3 endet, ist versionsabhängig.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Unter Debian/Ubuntu `adduser` verwenden,** wenn kein Skript nötig ist.
2. **Bei `useradd` immer `-m` und `-s`** angeben.
3. **Danach sofort `passwd`** ausführen.
4. **Mit `getent passwd` und `id` kontrollieren.**
5. **Zusatzgruppen sparsam vergeben.**
6. **`useradd -D` nur zum Anzeigen** nutzen.

### Prüfstand

- **Geprüfte Version:** shadow 4.13 (Ubuntu-Paket `passwd`); Debian-Manpage shadow 4.17.4.
- **Tatsächlich ausgeführt:** `useradd --help`, `useradd -D` (Anzeige ohne Root), Lesen von `HOME_MODE`, `UID_MIN`, `UID_MAX` aus `/etc/login.defs`.
- **Nicht ausgeführt:** jedes Anlegen eines Kontos, auch an Kopierdateien mit `-P`, weil Präfix-Tests bei `groupadd` echte Systemprotokolleinträge erzeugten.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `adduser` | Debian-Werkzeug mit Dialog; empfohlen für Einzelanlagen. |
| `passwd` | Setzt das Passwort des neuen Kontos. |
| `usermod` | Ändert vorhandene Konten. |
| `userdel`, `deluser` | Entfernen Konten. |
| `groupadd` | Legt Gruppen an. |
| `getent passwd`, `id` | Prüfen das Ergebnis. |

Ausgangseintrag: Datensatz 123 in `index.json` (`useradd`, Risiko „Gelb – Admin/Vorsicht“, Root „Häufig“). Der Hilfe-Platzhalter wurde durch die tatsächlichen Vorgaben unter Ubuntu, die Abgrenzung zu `adduser`, Optionen, Rückgabewerte und einen vollständigen Ablauf ersetzt.
