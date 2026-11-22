---
id: "chsh"
name: "chsh"
command: "chsh"
category: "Benutzer & Rechte"
language: "de"
root_required: false
risk_level: "caution"
tags: ["benutzer", "konten", "shell", "anmeldung"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 105
reviewed_at: "2026-11-13"
locally_checked_version: "shadow 4.13 (Paket passwd 1:4.13+dfsg1-4ubuntu3.2); nur Hilfe und Lesezugriffe"
---

# chsh – Anmelde-Shell eines Benutzerkontos ändern

## 1. Kurzbeschreibung

`chsh` („change shell“) legt fest, welches Programm nach der Anmeldung als Kommandozeile startet, zum Beispiel `/bin/bash`, `/usr/bin/zsh` oder `/usr/bin/fish`. Der Wert steht im siebten Feld des Kontoeintrags in `/etc/passwd`.

**Root-Rechte sind für das eigene Konto nicht nötig.** `chsh` ist als SUID-Programm installiert und fragt dein Passwort ab. Normale Benutzer dürfen nur Shells wählen, die in `/etc/shells` aufgeführt sind.

**Root-Rechte sind nötig**, um die Shell eines anderen Kontos zu ändern oder eine Shell einzutragen, die nicht in `/etc/shells` steht (etwa `/usr/sbin/nologin` für Dienstkonten).

## 2. Was macht der Befehl?

`chsh` ändert ausschließlich die Anmelde-Shell. Die aktuelle Sitzung läuft mit der bisherigen Shell weiter. Die neue Shell gilt für **neue Anmeldungen**, etwa eine Konsolenanmeldung, SSH oder nach erneutem Anmelden am Desktop. **Prüfpunkt:** Ob ein bereits laufendes Terminalprogramm neue Fenster sofort mit der neuen Shell öffnet, hängt vom Programm und seiner Einstellung ab.

Laut [Debian-Manpage zu chsh](https://manpages.debian.org/trixie/passwd/chsh.1.en.html) prüft `chsh` für normale Benutzer nur, ob die neue Shell in `/etc/shells` steht. Auf dem geprüften System verlangt die PAM-Konfiguration `/etc/pam.d/chsh` zusätzlich über `pam_shells`, dass auch die **aktuelle** Shell dort steht. Ein Konto mit `nologin` kann sich seine Shell deshalb nicht selbst zurückgeben.

### Implementierungen

Debian, Ubuntu und darauf aufbauende Systeme nutzen `chsh` aus der Shadow-Suite (Paket `passwd`). Andere Distributionen liefern `chsh` aus util-linux, das zusätzlich `-l`/`--list-shells` zum Auflisten der Shells kennt; siehe [util-linux-Manpage bei man7.org](https://man7.org/linux/man-pages/man1/chsh.1.html). **Prüfpunkt:** Mit `chsh --help` klären, welche Fassung vorliegt. Dieses Dokument beschreibt die Shadow-Fassung.

## 3. Syntax

```text
chsh [OPTIONEN] [KONTONAME]
```

- Ohne `KONTONAME` wird das eigene Konto geändert.
- Ohne `-s` fragt `chsh` die neue Shell interaktiv ab; die aktuelle steht in eckigen Klammern, eine leere Eingabe lässt sie unverändert.

```bash
chsh -s /usr/bin/zsh
sudo chsh -s /usr/sbin/nologin dienstkonto
```

Das bisherige NetMon-Beispiel `chsh --help` zeigt nur die Hilfe; der Platzhalter `chsh [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-s SHELL`, `--shell SHELL` | Neue Anmelde-Shell setzen. | Vollständigen Pfad angeben, wie er in `/etc/shells` steht. |
| `-h`, `--help` | Hilfe anzeigen. | Anders als bei `chfn` ist `-h` hier die Hilfe. |
| `-R VERZ`, `--root VERZ` | Änderung in einem anderen Wurzelverzeichnis vornehmen. | Nur absolute Pfade; für eingehängte Systemabbilder. |

Ein leerer Wert für `-s` lässt laut Manpage das System die Standard-Shell wählen. **Prüfpunkt:** Welche Shell das konkret ist, hängt von der Umgebung ab; nicht praktisch geprüft.

### Erlaubte Shells

```bash
cat /etc/shells
```

Auf dem geprüften System stehen dort unter anderem `/bin/bash`, `/usr/bin/bash`, `/bin/sh` und `/usr/bin/dash`. Wird eine Shell wie `zsh` über die Paketverwaltung installiert, trägt das Paket sie normalerweise selbst ein.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Die eigene Anmelde-Shell auf eine installierte, zugelassene Shell umstellen. Das ändert das eigene Konto und ist deshalb nur ein **Beispielszenario**; es wurde für dieses Dokument nicht ausgeführt.

### Schritt 1: Aktuelle Shell anzeigen

```bash
getent passwd "$USER" | cut -d: -f7
```

Das zeigt den gespeicherten Wert, zum Beispiel `/bin/bash`. `echo $SHELL` zeigt dagegen den Wert der laufenden Sitzung, der nach einer Änderung noch veraltet sein kann.

### Schritt 2: Neue Shell prüfen

```bash
grep -x /usr/bin/zsh /etc/shells
/usr/bin/zsh -c 'echo funktioniert'
```

Die erste Zeile prüft, ob der genaue Pfad zugelassen ist. Die zweite startet die Shell einmal testweise. Fehlt eine der Ausgaben, ist die Shell nicht installiert oder nicht eingetragen.

### Schritt 3: Shell ändern

```bash
chsh -s /usr/bin/zsh
```

`chsh` fragt nach deinem Passwort und ändert dann den Eintrag.

### Schritt 4: Ergebnis kontrollieren, bevor du dich abmeldest

```bash
getent passwd "$USER" | cut -d: -f7
```

Erwartet: `/usr/bin/zsh`. **Melde dich erst ab, wenn du in einem zweiten Terminal oder per `su - "$USER"` geprüft hast, dass die Anmeldung mit der neuen Shell funktioniert.**

### Rückweg

```bash
chsh -s /bin/bash
```

## 6. Typische Anwendungsfälle

| Aufgabe | Aufruf | Rechte |
| --- | --- | --- |
| Eigene Shell wechseln | `chsh -s /usr/bin/fish` | eigenes Passwort |
| Dienstkonto sperren | `sudo chsh -s /usr/sbin/nologin dienst` | Root |
| Shell eines Benutzers zurücksetzen | `sudo chsh -s /bin/bash anna` | Root |
| Systemabbild anpassen | `sudo chsh -R /mnt/abbild -s /bin/bash anna` | Root |

`nologin` verhindert interaktive Anmeldungen, ist aber keine vollständige Kontosperre: Andere Zugänge wie Dateiübertragung oder Dienste können je nach Konfiguration weiter funktionieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Aussperren

Eine Shell, die nicht startet oder sofort endet, verhindert die Anmeldung auf Konsole und per SSH. Grafische Sitzungen können ebenfalls betroffen sein, weil Anmeldeskripte teils über die Shell laufen. Ein normaler Benutzer kann sich dann nur noch über einen anderen Weg oder mit Hilfe der Verwaltung retten.

### Eingeschränkte Shells

Die Manpage rät davon ab, eingeschränkte Shells wie `rsh` in `/etc/shells` einzutragen, weil man sich sonst nicht mehr zurückstellen kann. Auf dem geprüften System steht `/bin/rbash` in `/etc/shells`. **Prüfpunkt:** Ob ein Benutzer aus `rbash` heraus `chsh` noch erfolgreich aufrufen kann, wurde nicht geprüft; wähle `rbash` nicht zum Ausprobieren.

### Skripte und Umgebung

Eine andere Shell liest andere Startdateien (`.bashrc` gegenüber `.zshrc` und anderen). Umgebungsvariablen, Aliase und `PATH`-Ergänzungen fehlen dann zunächst.

### SUID-Programm

`chsh` ändert `/etc/passwd` mit Root-Rechten. Die Einschränkung auf `/etc/shells` und die Passwortabfrage sind die Schutzmechanismen.

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt bestehen: Der Befehl löscht keine Daten, kann aber den eigenen Zugang blockieren.

## 8. Häufige Fehler

| Meldung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| `chsh: /usr/bin/xyz is an invalid shell` | Pfad nicht in `/etc/shells`. | Genauen Pfad aus `/etc/shells` nehmen; Shell über Paketverwaltung installieren. |
| `chsh: Warning: ... does not exist` | Root hat einen nicht vorhandenen Pfad gesetzt. | Sofort korrigieren, sonst ist keine Anmeldung möglich. |
| `chsh: Warning: ... is not executable` | Pfad ist keine ausführbare Datei. | Pfad prüfen. |
| `chsh: PAM: Authentication failure` | Falsches Passwort oder aktuelle Shell nicht in `/etc/shells`. | Passwort prüfen; bei `nologin` hilft nur die Verwaltung. |
| `You may not change the shell for '...'.` | Fremdes Konto ohne Root-Rechte. | Nur das eigene Konto ändern oder Verwaltung fragen. |
| `chsh: user '...' does not exist in /etc/passwd` | Konto aus LDAP, SSSD oder einem Verzeichnisdienst. | Änderung dort vornehmen. |

Die Meldungstexte wurden mit den englischen Meldungen im lokalen Programm abgeglichen. Ausgelöst wurde nur `option requires an argument -- 's'`.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Shell zuerst testweise starten,** etwa mit `zsh` im laufenden Terminal, bevor du sie zur Anmelde-Shell machst.
2. **Nur Pfade aus `/etc/shells` verwenden.**
3. **Ein zweites Terminal offen lassen** und die neue Anmeldung prüfen, bevor du dich abmeldest.
4. **Kein `sudo chsh` für das eigene Konto,** das umgeht die Prüfung gegen `/etc/shells`.
5. **Den alten Wert notieren** (`getent passwd "$USER" | cut -d: -f7`).

### Prüfstand

- **Geprüfte Version:** shadow 4.13 (Ubuntu-Paket `passwd`).
- **Tatsächlich ausgeführt:** `chsh --help`, `chsh -s` ohne Argument (Fehlermeldung), Lesen von `/etc/shells`, `/etc/pam.d/chsh` und der eigenen Anmelde-Shell, Abgleich der Meldungstexte im Programm.
- **Nicht ausgeführt:** jede Änderung einer Shell, also das Beispiel aus Abschnitt 5, `-R`, leerer Shell-Wert sowie das Verhalten mit `rbash`.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `chfn` | Ändert Name und Kontaktfelder desselben Kontoeintrags. |
| `usermod -s` | Setzt die Shell als Verwaltungsbefehl. |
| `getent passwd` | Zeigt den gespeicherten Kontoeintrag. |
| `passwd` | Ändert Passwort und Passwortstatus. |
| `su`, `sudo -i` | Starten Sitzungen eines anderen Kontos mit dessen Shell. |

Ausgangseintrag: Datensatz 105 in `index.json` (`chsh`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch die Regeln von `/etc/shells` und `pam_shells`, den Zeitpunkt der Wirkung, das Aussperrrisiko und einen vorsichtigen Ablauf ersetzt.
