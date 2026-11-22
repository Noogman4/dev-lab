---
id: "chmod"
name: "chmod"
command: "chmod"
category: "Benutzer & Rechte"
language: "de"
root_required: false
risk_level: "caution"
tags: ["benutzer", "rechte", "dateirechte", "modus"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 103
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# chmod – Zugriffsrechte von Dateien und Ordnern festlegen

## 1. Kurzbeschreibung

`chmod` („change mode“) ändert die Rechtebits einer Datei oder eines Ordners: wer lesen, schreiben oder ausführen darf. Außerdem setzt es die Sonderbits setuid, setgid und Sticky-Bit.

**Root-Rechte sind für eigene Dateien nicht nötig.** Nur der Eigentümer einer Datei (oder Root) darf ihre Rechte ändern. Für Dateien anderer Konten, etwa unter `/etc` oder `/usr`, sind Root-Rechte nötig – dort ist ein Fehler aber auch besonders folgenreich.

## 2. Was macht der Befehl?

Jede Datei hat drei Rechtegruppen:

| Kürzel | Wer | Beispiel in `ls -l` |
| --- | --- | --- |
| `u` (user) | Eigentümer | erste Dreiergruppe `rw-` |
| `g` (group) | Mitglieder der Besitzergruppe | zweite Dreiergruppe |
| `o` (others) | alle anderen | dritte Dreiergruppe |
| `a` (all) | alle drei zusammen | – |

Jede Gruppe kann `r` (lesen), `w` (schreiben) und `x` (ausführen) haben. Bei Ordnern bedeutet `r` „Inhalt auflisten“, `w` „Einträge anlegen, umbenennen oder löschen“ und `x` „hineinwechseln und Einträge erreichen“.

`chmod` verändert nur diese Metadaten, nicht den Dateiinhalt. Eine Änderung wirkt sofort für neue Zugriffe; bereits geöffnete Dateien bleiben meist zugänglich.

Grundlage sind die [Debian-Manpage zu chmod](https://manpages.debian.org/trixie/coreutils/chmod.1.en.html) und die lokale Hilfe von GNU coreutils 9.4. Andere Implementierungen (BusyBox, BSD) kennen die Modi ebenfalls, haben aber teils andere Optionen.

### Zwei Schreibweisen

**Symbolisch:** `[ugoa][+-=][rwxXst]`, mehrere Angaben durch Komma getrennt. `+` fügt hinzu, `-` entfernt, `=` setzt genau und entfernt alles nicht Genannte.

**Oktal:** Ziffern aus den Werten 4 (r), 2 (w) und 1 (x), je eine Ziffer für u, g und o. Eine optionale vierte, vorangestellte Ziffer steht für setuid (4), setgid (2) und Sticky (1).

| Oktal | Symbolisch | Typische Verwendung |
| --- | --- | --- |
| `600` | `rw-------` | Private Datei, z. B. Schlüssel |
| `644` | `rw-r--r--` | Für alle lesbare Datei |
| `700` | `rwx------` | Privater Ordner oder Skript |
| `755` | `rwxr-xr-x` | Programm oder öffentlich lesbarer Ordner |
| `1777` | `rwxrwxrwt` | Gemeinsamer Ordner wie `/tmp` (Sticky-Bit) |

## 3. Syntax

```text
chmod [OPTIONEN] MODUS[,MODUS] DATEI ...
chmod [OPTIONEN] OKTALMODUS DATEI ...
chmod [OPTIONEN] --reference=VORLAGE DATEI ...
```

```bash
chmod u+x skript.sh
chmod 600 geheim.txt
chmod -R u=rwX,go=rX freigabe
```

Das bisherige NetMon-Beispiel `chmod --help` zeigt nur die Hilfe; der Platzhalter `chmod [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option oder Zeichen | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-R`, `--recursive` | Ordner samt Inhalt bearbeiten. | Größte Fehlerquelle; Ziel genau prüfen. |
| `-c`, `--changes` | Nur tatsächliche Änderungen melden. | Zeigt alten und neuen Modus. |
| `-v`, `--verbose` | Jede Datei melden. | Viel Ausgabe bei großen Bäumen. |
| `-f`, `--silent` | Fehlermeldungen weitgehend unterdrücken. | Versteckt Probleme. |
| `--reference=VORLAGE` | Modus einer anderen Datei übernehmen. | Vorlage vorher mit `stat` prüfen. |
| `--preserve-root` | Rekursive Arbeit auf `/` verweigern. | Bei GNU `chmod` nicht Standard. |
| `X` im Modus | `x` nur für Ordner und für Dateien, die schon für irgendwen ausführbar sind. | Ideal für `-R`, damit Textdateien nicht ausführbar werden. |
| `s` im Modus | setuid (`u+s`) beziehungsweise setgid (`g+s`). | Sicherheitsrelevant, siehe Abschnitt 7. |
| `t` im Modus | Sticky-Bit; in Ordnern dürfen nur Eigentümer ihre Einträge löschen. | Typisch für gemeinsame Ordner. |

**Versionshinweis:** Neuere coreutils (die Debian-Manpage beschreibt 9.7) kennen zusätzlich `-h`/`--no-dereference`, `--dereference` sowie `-H`, `-L`, `-P` zur Linkbehandlung bei `-R`. Die lokal geprüfte Version 9.4 bietet diese Optionen für `chmod` nicht an. **Prüfpunkt:** Verfügbarkeit mit `chmod --help` prüfen.

### Wirkung ohne `u`, `g`, `o` oder `a`

`chmod +r datei` wirkt wie `a+r`, **lässt aber Bits aus, die die aktuelle umask sperrt**. Im Test mit umask `0007` ergab `chmod +r` den Modus `640`, `chmod a+r` dagegen `644`. Schreibe `a`, wenn alle gemeint sind.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Ein eigenes Skript ausführbar machen, eine Notiz privat stellen und einen Ordner so freigeben, dass nur Ordner und Programme ausführbar werden.

### Schritt 1: Übungsordner und Dateien anlegen

```bash
uebung="$(mktemp -d -t netmon-chmod-XXXXXX)" || exit 1
cd "$uebung" || exit 1
printf '#!/bin/sh\necho hallo\n' > skript.sh
printf 'privat\n' > notiz.txt
ls -l
```

Neue Dateien sind zunächst nicht ausführbar. Welche Rechte sie genau haben, hängt von deiner umask ab.

### Schritt 2: Skript ausführbar machen

```bash
./skript.sh
chmod -v u+x skript.sh
./skript.sh
```

Der erste Aufruf scheitert mit `Permission denied` (Rückgabewert 126). `u+x` ergänzt nur das Ausführrecht für dich. `-v` meldet zum Beispiel `mode of 'skript.sh' changed from 0660 (rw-rw----) to 0760 (rwxrw----)`. Danach gibt das Skript `hallo` aus.

### Schritt 3: Notiz privat stellen

```bash
chmod -c 600 notiz.txt
stat -c '%a %A %n' notiz.txt
```

`600` erlaubt nur dir Lesen und Schreiben. `stat` zeigt `600 -rw------- notiz.txt`. Ein zweiter gleicher Aufruf mit `-c` gibt nichts aus, weil sich nichts ändert.

### Schritt 4: Ordner sinnvoll freigeben

```bash
mkdir -p baum/sub
touch baum/text baum/sub/text2
chmod -R u=rwX,go=rX baum
find baum -printf '%m %p\n'
```

Ordner erhalten `755`, normale Dateien `644`. Großes `X` setzt `x` nur bei Ordnern und Dateien, die bereits ausführbar waren. Im Test wurde eine vorher mit `700` versehene Datei deshalb zu `755` – das ist gewollt, aber zu beachten.

## 6. Typische Anwendungsfälle

| Aufgabe | Aufruf |
| --- | --- |
| Skript ausführbar machen | `chmod u+x skript.sh` |
| SSH-Schlüssel schützen | `chmod 600 ~/.ssh/id_ed25519` |
| Webinhalte lesbar machen | `chmod -R u=rwX,go=rX public_html` |
| Gruppenordner mit Gruppenvererbung | `chmod 2770 projekt` |
| Schreibrecht für andere entziehen | `chmod o-w datei` |

Das setgid-Bit an Ordnern lässt neue Einträge die Ordnergruppe erben. Laut [GNU-Handbuch zu setuid/setgid bei Ordnern](https://www.gnu.org/software/coreutils/manual/html_node/Directory-Setuid-and-Setgid.html) entfernt ein normaler Oktalmodus wie `750` diese Bits bei Ordnern nicht. Im Test blieb `drwxr-s---` nach `chmod 750` erhalten; erst `chmod 00750` entfernte das setgid-Bit.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Daten freigeben

`chmod 777` oder `o+w` erlaubt jedem lokalen Konto das Ändern und bei Ordnern auch das Löschen von Einträgen. Bei privaten Schlüsseln, Passwortdateien oder Konfigurationen mit Zugangsdaten führt `o+r` zur Datenoffenlegung. Programme wie `ssh` verweigern Schlüssel mit zu offenen Rechten.

### Rekursive Änderungen

`chmod -R` auf einen falschen Pfad ändert sofort viele Dateien. Es gibt keine Rückgängig-Funktion und meist keine Aufzeichnung der vorherigen Rechte. Mit `sudo chmod -R ... /` oder Systemordnern lassen sich Anmeldung, `sudo` und Dienste unbrauchbar machen.

### Sonderbits

setuid- oder setgid-Programme laufen mit den Rechten ihres Eigentümers beziehungsweise ihrer Gruppe. Ein unbedacht gesetztes `u+s` auf ein Programm von Root kann eine Rechteausweitung ermöglichen. Setze diese Bits nur, wenn ein Programm dafür ausgelegt ist.

### Sich selbst aussperren

`chmod 0 datei` entzieht auch dir das Lesen. Als Eigentümer kannst du die Rechte zwar wieder ändern, Programme scheitern aber bis dahin. Ein Ordner ohne `x` ist nicht mehr betretbar.

### Risikoeinstufung

Die ursprüngliche Einstufung „Rot – destruktiv/möglich kritisch“ trifft auf rekursive oder privilegierte Änderungen an Systempfaden zu. Der dokumentierte Normalfall – Rechte eigener Dateien gezielt setzen – löscht keine Daten und ist umkehrbar. Der Kopf verwendet deshalb `caution`; die oben genannten Fälle bleiben ausdrücklich kritisch.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| `chmod: changing permissions of '...': Operation not permitted` | Datei gehört dir nicht. | Eigentümer mit `ls -l` prüfen; nur bei berechtigtem Anlass mit Verwaltungsrechten. |
| `chmod: invalid mode: '999'` | Ziffern über 7 oder unbekannte Buchstaben. | Oktal nur 0–7; Buchstaben nur `rwxXst` bzw. `ugoa`. |
| `+r` wirkt nicht für alle | umask sperrt Bits, weil kein `a` angegeben wurde. | `a+r` schreiben. |
| Alle Dateien plötzlich ausführbar | `-R` mit `x` statt `X`. | Mit `u=rwX,go=rX` neu setzen; Programme danach gezielt prüfen. |
| setgid am Ordner bleibt trotz `chmod 750` | Absichtliches GNU-Verhalten bei Ordnern. | `g-s` oder fünfstelligen Oktalmodus (`00750`) verwenden. |
| `Permission denied` beim Ausführen | `x` fehlt oder Dateisystem mit `noexec` eingehängt. | `ls -l` und `findmnt -T DATEI` prüfen. |

Rückgabewert: `0` bei Erfolg, `1` bei Fehlern (geprüft für ungültige Modi).

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Vorher anzeigen:** `stat -c '%a %A %n' DATEI` zeigt Oktal- und Symbolform.
2. **Symbolisch und gezielt ändern** (`u+x`, `o-w`) statt pauschaler Oktalwerte.
3. **Bei `-R` immer `X` statt `x` verwenden.**
4. **Nie `777`** als Lösung für Rechteprobleme; erst klären, wer genau Zugriff braucht.
5. **Rechte vor großen Änderungen sichern,** zum Beispiel mit `getfacl -R ordner > rechte.txt`.
6. **`-c` zur Kontrolle nutzen** und Systemordner meiden.

### Prüfstand

- **Geprüfte Version:** GNU coreutils 9.4.
- **Tatsächlich ausgeführt** in einem eigenen Testordner: `u+x` mit vorher/nachher Ausführung, `600` mit `-c` (einschließlich Wiederholung ohne Ausgabe), `+r` unter umask `0007` gegen `a+r`, `-R u=rwX,go=rX`, `--reference`, ungültige Modi `999` und `u+q` (Rückgabe 1), Erhalt des setgid-Bits am Ordner bei `750` und Entfernen mit `00750`, Leseverweigerung nach `chmod 0`.
- **Nicht geprüft:** Aufrufe mit Root-Rechten, setuid an Programmen, Symlink-Optionen neuerer Versionen, `noexec`-Dateisysteme.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `chown`, `chgrp` | Ändern Eigentümer und Gruppe, für die die Rechte gelten. |
| `umask` | Legt fest, welche Rechte neue Dateien nicht erhalten. |
| `stat`, `ls -l` | Zeigen die aktuellen Rechte. |
| `setfacl`, `getfacl` | Feinere Rechte für einzelne Benutzer und Gruppen. |
| `install -m` | Kopiert eine Datei und setzt dabei den Modus. |
| `find -perm` | Sucht Dateien nach Rechten, etwa für eine Bestandsaufnahme. |

Ausgangseintrag: Datensatz 103 in `index.json` (`chmod`, Risiko „Rot – destruktiv/möglich kritisch“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch beide Modusschreibweisen, `X`, Sonderbits, das umask-Verhalten und einen geprüften Ablauf ersetzt. Die Risikostufe wurde für den Normalfall auf „Vorsicht“ gesenkt und die kritischen Fälle wurden einzeln benannt.
