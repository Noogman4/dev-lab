---
id: "newgrp"
name: "newgrp"
command: "newgrp"
category: "Benutzer & Rechte"
language: "de"
root_required: false
risk_level: "caution"
tags: ["benutzer", "gruppen", "sitzung", "shadow"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 115
reviewed_at: "2026-11-13"
locally_checked_version: "shadow 4.13 (Paket login 1:4.13+dfsg1-4ubuntu3.2)"
---

# newgrp – Neue Shell mit einer anderen aktiven Gruppe starten

## 1. Kurzbeschreibung

`newgrp` startet eine neue Shell, in der eine andere Gruppe die **aktive (primäre) Gruppe** ist. Rechteprüfungen berücksichtigen diese Gruppe. Neue Dateien erhalten häufig diese Gruppe; ein setgid-Verzeichnis oder Dateisystemregeln können stattdessen die Gruppe des übergeordneten Verzeichnisses vorgeben. Häufigster Anlass: Du wurdest gerade einer Gruppe hinzugefügt und willst sie nutzen, ohne dich neu anzumelden.

**Root-Rechte sind nicht nötig.** Die übliche Installation von `newgrp` verwendet SUID-Rechte. Gruppenmitglieder können normalerweise ohne Passwort wechseln. Laut Shadow-Manpage gibt es eine Ausnahme: Hat das Benutzerkonto kein Passwort, die Gruppe aber schon, kann auch für Mitglieder eine Abfrage erfolgen. Nichtmitglieder benötigen ein gesetztes Gruppenpasswort.

## 2. Was macht der Befehl?

`newgrp GRUPPE` prüft deine Berechtigung, ändert die aktive Gruppen-ID und versucht, die Gruppe in die Liste der Zusatzgruppen aufzunehmen. Danach startet es deine Anmelde-Shell neu. Ohne `-` bleiben Arbeitsordner und Umgebung erhalten. Mit `exit` kehrst du zur vorherigen Shell zurück.

Regeln laut [Debian-Manpage zu newgrp (shadow 4.13)](https://manpages.debian.org/bookworm/login/newgrp.1.en.html):

| Situation | Ergebnis |
| --- | --- |
| Du bist Mitglied der Gruppe | Normalerweise Wechsel ohne Passwort; Ausnahme: Konto ohne Passwort, Gruppe mit Passwort. |
| Kein Mitglied, Gruppe hat ein Passwort | Passwortabfrage. |
| Kein Mitglied, Gruppenpasswort leer oder gesperrt | Zugriff verweigert. |
| Kein Gruppenname angegeben | Zurück zur primären Gruppe aus `/etc/passwd`. |

`newgrp` ändert **keine** Konten oder Gruppendateien. Die Wirkung betrifft nur die neu gestartete Shell und deren Unterprozesse.

### Zwei Implementierungen

Ubuntu 24.04 und Debian bis bookworm liefern `newgrp` aus der Shadow-Suite mit der Syntax `newgrp [-] [gruppe]`. Debian trixie liefert stattdessen die util-linux-Fassung, die zusätzlich `-c BEFEHL` kennt, aber kein `-` beschreibt; siehe [Debian-Manpage trixie](https://manpages.debian.org/trixie/login/newgrp.1.en.html). **Prüfpunkt:** Welche Fassung vorliegt, zeigt `newgrp --help` beziehungsweise die Manpage.

## 3. Syntax

```text
newgrp [-] [GRUPPE]
```

- `-` initialisiert die Umgebung neu, als hättest du dich angemeldet (Shadow-Fassung).
- Ohne Gruppe: zurück zur Anmeldegruppe.

```bash
newgrp users
newgrp - projekt
newgrp
```

Das bisherige NetMon-Beispiel `newgrp --help` ist in der Shadow-Fassung keine echte Hilfeoption: Es gibt nur die Zeile `Usage: newgrp [-] [group]` aus. Der Platzhalter `newgrp [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Fassung | Bedeutung |
| --- | --- | --- |
| `-` | Shadow | Umgebung wie bei einer Anmeldung neu aufbauen. |
| `GRUPPE` | beide | Ziel-Gruppe; ohne Angabe die Anmeldegruppe. |
| `-c BEFEHL`, `--command=BEFEHL` | util-linux | Befehl statt interaktiver Shell ausführen. |
| `-h`, `--help`, `-V`, `--version` | util-linux | Hilfe und Version. |

Für einen einzelnen Befehl mit anderer Gruppe gibt es in der Shadow-Suite `sg GRUPPE -c 'BEFEHL'`. Auf dem geprüften System ist `sg` ein Verweis auf `newgrp`.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Eine Datei direkt mit der Gruppe `users` anlegen, ohne `chgrp` zu benutzen. Voraussetzung: Du bist Mitglied von `users` (prüfen mit `id -nG`).

### Schritt 1: Übungsordner und aktuelle Gruppe

```bash
uebung="$(mktemp -d -t netmon-newgrp-XXXXXX)" && cd "$uebung" || exit 1
id -gn
```

`id -gn` zeigt die aktive Gruppe, meist gleichnamig mit deinem Konto.

### Schritt 2: Shell mit anderer Gruppe

```bash
newgrp users
```

Es öffnet sich eine neue Shell; die Eingabeaufforderung sieht unverändert aus.

### Schritt 3: Wirkung prüfen

```bash
id -gn
touch neu
stat -c '%G %n' neu
exit
```

`id -gn` zeigt nun `users`, und die neue Datei gehört der Gruppe `users`. `exit` beendet die Zusatz-Shell; danach ist wieder die ursprüngliche Gruppe aktiv.

Im Test wurden die Befehle aus Schritt 3 über eine Pipe an `newgrp users` übergeben. Ergebnis: `users` und `users neu`, Rückgabewert `0`. Danach zeigte die äußere Shell weiter die Ursprungsgruppe.

## 6. Typische Anwendungsfälle

- **Neue Mitgliedschaft sofort nutzen:** Nach einer freigegebenen Aufnahme in eine Projektgruppe kann deren Mitglied mit `newgrp projekt` in einem Terminal arbeiten, ohne sich abzumelden. Bereits laufende andere Programme behalten ihre bisherigen Gruppen.
- **Dateien für eine Gruppe anlegen:** Die neue Shell verwendet die gewählte Gruppe; setgid-Verzeichnisse und Dateisystemregeln können die Dateigruppe anders bestimmen. Siehe [chown(2)](https://manpages.debian.org/trixie/manpages-dev/chown.2.en.html).
- **Gruppenpasswort nutzen:** Nichtmitglieder können mit dem Gruppenpasswort vorübergehend beitreten (selten und sicherheitlich fragwürdig).

## 7. Risiken, Nebenwirkungen und Vorsicht

`newgrp` bearbeitet keine Konten- oder Gruppendatenbank, verändert aber die wirksamen Gruppenrechte einer neuen Shell. Deshalb bleibt die Einstufung `caution` (Admin/Vorsicht) bestehen. Programme in dieser Shell können mit diesen Rechten Dateien lesen, verändern oder Dienste steuern.

- **Mächtige Gruppen:** Zugriff auf den Socket eines gewöhnlichen Docker-Dienstes über die Gruppe `docker` entspricht Root-Rechten. Ein Gruppenwechsel ist deshalb keine bloße Anzeigeaktion; siehe auch [docker](docker.md).

- **Verschachtelte Shells:** Jeder Aufruf startet eine weitere Shell. Wer das vergisst, landet nach mehreren `newgrp` in tief verschachtelten Sitzungen. `exit` beendet jeweils nur eine Stufe.
- **Ohne `-` bleibt die Umgebung,** mit `-` werden Variablen wie bei einer Anmeldung neu gesetzt; Arbeitsordner und Aliase können sich dann ändern.
- **Gruppenpasswörter** sind geteilte Geheimnisse und ein Sicherheitsrisiko.
- **Protokolleinträge:** Mit `SYSLOG_SG_ENAB yes` (auf dem geprüften System gesetzt) protokolliert `newgrp` jeden Wechsel im Systemprotokoll, etwa `user 'happy' ... switched to group ...`.
- **Skripte:** Die neue Shell übernimmt die Standardeingabe und kann auf Eingaben warten oder daraus weitere Befehle lesen. Nicht auf einen einfachen Rücksprung wie bei einem gewöhnlichen Hilfsbefehl verlassen. Für einzelne Aktionen `sg GRUPPE -c '...'` verwenden und dessen Berechtigungen prüfen.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `newgrp: group '...' does not exist` | Tippfehler oder Gruppe nicht vorhanden. | `getent group NAME` prüfen. |
| Passwortabfrage, obwohl Mitglied | Etwa Konto ohne Passwort bei gesetztem Gruppenpasswort; möglicherweise abweichende Mitgliedschaft in der Kontenquelle. | Mitgliedschaft und Richtlinie durch die Verwaltung prüfen lassen; keine Passwortdateien veröffentlichen. |
| `Password:` und danach Ablehnung | Kein Mitglied, falsches oder kein Gruppenpasswort. | Verwaltung um Mitgliedschaft bitten. |
| Skript hängt bei `newgrp` | Interaktive Shell wartet auf Eingaben. | `sg GRUPPE -c 'befehl'` nutzen. |
| `-c` unbekannt | Shadow-Fassung. | `sg` verwenden. |

Im Test endete ein Aufruf mit unbekannter Gruppe mit Rückgabewert `1`.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **`id -gn` vor und nach dem Wechsel** prüfen.
2. **Mit `exit` zurückkehren,** statt mehrfach `newgrp` aufzurufen.
3. **Für einzelne Befehle `sg` verwenden.**
4. **Eine Neuanmeldung lädt die aktuellen Gruppen in eine neue Sitzung.** `newgrp` ändert keine Mitgliedschaft dauerhaft und aktualisiert keine bereits laufenden anderen Programme.

### Prüfstand

- **Geprüfte Version:** shadow 4.13 (Ubuntu-Paket `login`).
- **Tatsächlich ausgeführt** im Testordner: `newgrp users` mit Befehlen über eine Pipe (aktive Gruppe und Dateigruppe `users`, Rückgabe 0), unbekannte Gruppe (Rückgabe 1), `newgrp -`, `newgrp --help`. Die Wechsel erzeugten Einträge im Systemprotokoll.
- **Nicht geprüft:** Gruppenpasswort-Abfrage, die util-linux-Fassung mit `-c`, Verhalten in grafischen Terminals.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `sg` | Führt einen einzelnen Befehl mit anderer Gruppe aus. |
| `id`, `groups` | Zeigen aktive und zusätzliche Gruppen. |
| `gpasswd` | Verwaltet Mitglieder und Gruppenpasswörter. |
| `usermod -aG` | Fügt einen Benutzer dauerhaft zu Gruppen hinzu. |
| `chgrp` | Ändert die Gruppe vorhandener Dateien. |
| `su`, `sudo` | Wechseln den Benutzer statt nur die Gruppe. |

Ausgangseintrag: Datensatz 115 in `index.json` (`newgrp`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Berechtigungsregeln, die beiden Implementierungen und einen geprüften Ablauf ersetzt. Bei der Integrationsprüfung wurde die zwischenzeitliche Herabstufung auf „sicher“ korrigiert: Gruppenrechte und Protokolleinträge sind relevante Nebenwirkungen. Die oben beschriebenen praktischen Tests stammen aus der Erstellung; bei der Integration wurde kein erneuter Gruppenwechsel ausgeführt.
