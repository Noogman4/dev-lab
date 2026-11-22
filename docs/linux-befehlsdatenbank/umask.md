---
id: "umask"
name: "umask"
command: "umask"
category: "Benutzer & Rechte"
language: "de"
root_required: false
risk_level: "caution"
tags: ["benutzer", "rechte", "dateirechte", "shell"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel in Unter-Shell geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 122
reviewed_at: "2026-11-13"
locally_checked_version: "GNU bash 5.2.21 (Shell-Builtin umask)"
---

# umask – Standardrechte für neu angelegte Dateien festlegen

## 1. Kurzbeschreibung

`umask` zeigt oder setzt die **Dateierstellungsmaske** der aktuellen Shell. Sie legt fest, welche Rechte neue Dateien und Ordner **nicht** erhalten. Eine umask von `022` bedeutet zum Beispiel: Gruppe und andere bekommen kein Schreibrecht.

**Root-Rechte sind nicht nötig.** Jeder Prozess hat seine eigene umask und darf sie selbst ändern. Eine Änderung wirkt nur auf die aktuelle Shell und die Programme, die sie danach startet – nicht auf bereits vorhandene Dateien und nicht auf andere Sitzungen.

`umask` ist ein **eingebauter Shell-Befehl** (Builtin). Auf dem geprüften System gibt es kein eigenständiges Programm `/usr/bin/umask`; `type umask` meldet eine von der Shell mitgelieferte Funktion. Das ist zwingend so, denn ein externes Programm könnte die umask der aufrufenden Shell nicht ändern.

## 2. Was macht der Befehl?

Programme legen Dateien mit einem gewünschten Modus an: normale Dateien meist `666` (`rw-rw-rw-`), Ordner `777`. Der Kernel entfernt davon alle Bits, die in der umask gesetzt sind. Das beschreibt die [Debian-Manpage zum Systemaufruf umask(2)](https://manpages.debian.org/trixie/manpages-dev/umask.2.en.html).

| umask | Neue Datei | Neuer Ordner | Typische Verwendung |
| --- | --- | --- | --- |
| `022` | `644` (`rw-r--r--`) | `755` | Klassischer Standard; alle dürfen lesen. |
| `002` | `664` | `775` | Gruppenarbeit mit persönlicher Gruppe. |
| `007` | `660` | `770` | Gruppe darf alles, andere nichts. |
| `027` | `640` | `750` | Gruppe darf lesen, andere nichts. |
| `077` | `600` | `700` | Nur der Eigentümer. |

Die umask kann Rechte nur **wegnehmen**, nie hinzufügen. Eine Textdatei wird durch `umask 000` nicht ausführbar, weil das Programm `x` gar nicht angefordert hat.

**Ausnahme:** Hat der übergeordnete Ordner eine Vorgabe-ACL, wird die umask laut umask(2) ignoriert; dann bestimmt die ACL die Rechte.

### Woher kommt der Startwert?

Auf Debian/Ubuntu setzt das PAM-Modul `pam_umask` den Wert bei der Anmeldung. Grundlage ist `UMASK` in `/etc/login.defs` (auf dem geprüften System `027`). Weil dort zusätzlich `USERGROUPS_ENAB yes` gilt, erhalten Konten mit gleichnamiger persönlicher Gruppe für die Gruppe dieselben Rechte wie für den Eigentümer. Ergebnis im Test: `0007`. **Prüfpunkt:** Desktop-Umgebungen, `~/.profile` oder systemd-Einstellungen können den Wert zusätzlich verändern.

## 3. Syntax

```text
umask [-p] [-S] [MODUS]
```

- Ohne `MODUS`: aktuelle Maske anzeigen.
- `MODUS` mit Ziffer am Anfang: Oktalzahl, zum Beispiel `027`.
- Sonst: symbolische Form wie bei `chmod`, die die **erlaubten** Rechte beschreibt, zum Beispiel `u=rwx,g=rx,o=`.

```bash
umask
umask -S
umask 077
```

Das bisherige NetMon-Beispiel `umask --help` zeigt in Bash 5.2 dieselbe Kurzhilfe wie `help umask`. In anderen Shells (etwa dash) ist `--help` nicht garantiert; `help umask` ist dann ebenfalls Bash-spezifisch. Der Platzhalter `umask [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Beispielausgabe |
| --- | --- | --- |
| *(keine)* | Maske oktal anzeigen. | `0007` |
| `-S` | Erlaubte Rechte symbolisch anzeigen. | `u=rwx,g=rwx,o=` |
| `-p` | Ausgabe als wiederverwendbarer Befehl. | `umask 0007` |
| `MODUS` | Neue Maske setzen. | – |

Die Optionen folgen dem Abschnitt zu `umask` in der [Debian-Manpage zu bash](https://manpages.debian.org/trixie/bash/bash.1.en.html) und der lokalen Hilfe `help umask`. Andere Shells (dash, zsh, fish) bieten `umask` ebenfalls an; `-p` ist nicht überall vorhanden. **Prüfpunkt:** in anderen Shells nicht geprüft.

**Achtung bei der symbolischen Form:** `umask -S` und `umask u=rwx,g=rx,o=` beschreiben die erlaubten Rechte, die Oktalform beschreibt die **verbotenen**. Im Test ergab `umask u=rwx,g=rx,o=` den Oktalwert `0027`.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Die Wirkung verschiedener Masken sehen, ohne die eigene Sitzung dauerhaft zu ändern. Dazu läuft alles in einer **Unter-Shell**, die danach endet.

### Schritt 1: Übungsordner und Unter-Shell

```bash
uebung="$(mktemp -d -t netmon-umask-XXXXXX)" || exit 1
cd "$uebung" || exit 1
bash
```

Ab hier wirken Änderungen nur in dieser neuen Shell.

### Schritt 2: Aktuellen Wert ansehen

```bash
umask
umask -S
```

### Schritt 3: Masken vergleichen

```bash
umask 022; touch a; mkdir d1
umask 077; touch b; mkdir d2
stat -c '%a %n' a d1 b d2
```

Ergebnis im Test: `644 a`, `755 d1`, `600 b`, `700 d2`.

### Schritt 4: Unter-Shell verlassen

```bash
exit
umask
```

Nach `exit` zeigt `umask` wieder den ursprünglichen Wert – die Änderungen galten nur in der Unter-Shell.

## 6. Typische Anwendungsfälle

- **Vertrauliche Arbeit:** `umask 077` vor dem Erzeugen von Schlüsseln oder Exporten, damit neue Dateien privat sind.
- **Skripte:** Am Anfang eines Skripts eine feste umask setzen, damit das Ergebnis nicht von der aufrufenden Umgebung abhängt.
- **Gruppenarbeit:** `umask 002` oder `007`, damit Gruppenmitglieder neue Dateien bearbeiten können.
- **Fehlersuche:** Wenn neue Dateien unerwartete Rechte haben, zuerst `umask` prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

- **Zu offene Maske:** `umask 000` erzeugt für alle beschreibbare Dateien und Ordner. Dauerhaft in `~/.bashrc` oder `~/.profile` eingetragen, kann das Daten offenlegen oder Manipulation erlauben.
- **Zu enge Maske:** `077` in gemeinsamen Projektordnern führt dazu, dass Kollegen neue Dateien nicht lesen können.
- **Verwechslung der Schreibweisen:** Oktal heißt „verbieten“, symbolisch heißt „erlauben“.
- **Programme mit eigenen Modi:** Manche Programme setzen Rechte nach dem Anlegen ausdrücklich mit `chmod`; dann wirkt die umask nicht.
- **Dauerhafte Änderungen** gehören in die dafür vorgesehenen Dateien (`/etc/login.defs`, `~/.profile`). Systemweite Änderungen betreffen alle Konten und sind Sache der Verwaltung.

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt als `caution` bestehen: Anzeigen ist harmlos, eine falsche dauerhafte Maske kann Daten offenlegen.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `umask: 999: Oktalzahl ist außerhalb des Gültigkeitsbereiches.` | Ziffern größer 7. | Nur Ziffern 0–7 verwenden; Rückgabewert war `1`. |
| Änderung wirkt in anderem Terminal nicht | umask gilt pro Prozess. | In jeder Sitzung setzen oder dauerhaft in `~/.profile`. |
| `sudo umask 022` ohne Wirkung | Wirkt nur im kurzlebigen Prozess von `sudo`. | `umask` in der eigenen Shell ausführen. |
| Neue Dateien haben trotzdem andere Rechte | Vorgabe-ACL im Ordner oder Programm setzt Rechte selbst. | `getfacl ORDNER` prüfen. |
| Keine Hilfe mit `umask --help` | Andere Shell als Bash. | Shell-Handbuch, etwa `man dash`. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Zum Ausprobieren eine Unter-Shell (`bash`) starten** und danach mit `exit` verlassen.
2. **`umask -S` lesen;** die symbolische Anzeige ist leichter verständlich.
3. **Für private Daten `077`,** für normale Arbeit den Systemwert lassen.
4. **Vorhandene Dateien mit `chmod` ändern,** nicht mit `umask`.
5. **In Skripten die gewünschte Maske ausdrücklich setzen.**

### Prüfstand

- **Geprüfte Version:** Bash 5.2 (Ubuntu 24.04-Basis), Builtin `umask`.
- **Tatsächlich ausgeführt** in einer Unter-Shell im Testordner: Anzeige (`0007`), `-S`, `-p`, Masken `022` und `077` mit Dateien und Ordnern, symbolische Form `u=rwx,g=rx,o=` (ergibt `0027`), ungültiger Wert `999` (Rückgabe 1). Außerdem `help umask`, `umask --help`, `type umask`, `UMASK` in `/etc/login.defs` und `pam_umask` in der PAM-Sitzung.
- **Nicht geprüft:** andere Shells, dauerhafte Änderungen in Profildateien, Wirkung in grafischen Sitzungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `chmod` | Ändert Rechte vorhandener Dateien. |
| `mkdir -m`, `install -m` | Setzen Rechte beim Anlegen ausdrücklich. |
| `setfacl -d` | Vorgabe-ACL, die die umask in einem Ordner ersetzt. |
| `stat`, `ls -l` | Zeigen die tatsächlich entstandenen Rechte. |
| `help` | Zeigt Hilfe zu Shell-Builtins. |

Ausgangseintrag: Datensatz 122 in `index.json` (`umask`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der Platzhalter wurde um die Einordnung als Shell-Builtin ergänzt. Ergänzt wurden die Rechenregel, Herkunft des Startwerts, die beiden Schreibweisen und ein geprüfter Ablauf.
