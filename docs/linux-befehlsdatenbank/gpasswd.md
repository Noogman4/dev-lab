---
id: "gpasswd"
name: "gpasswd"
command: "gpasswd"
category: "Benutzer & Rechte"
language: "de"
root_required: true
risk_level: "caution"
tags: ["benutzer", "gruppen", "kontenverwaltung", "gshadow"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 110
reviewed_at: "2026-11-13"
locally_checked_version: "shadow 4.13 (Paket passwd 1:4.13+dfsg1-4ubuntu3.2); nur Hilfe und Meldungstexte"
---

# gpasswd – Gruppenmitglieder, Gruppenverwalter und Gruppenpasswort verwalten

## 1. Kurzbeschreibung

`gpasswd` verwaltet lokale Gruppen in `/etc/group` und `/etc/gshadow`. Am häufigsten wird es benutzt, um **einen Benutzer zu einer Gruppe hinzuzufügen oder daraus zu entfernen**. Außerdem kann es Gruppenverwalter festlegen und ein Gruppenpasswort setzen.

**Für den Normalfall sind Root-Rechte nötig.** Ausnahme: Ein in `/etc/gshadow` eingetragener **Gruppenverwalter** darf Mitglieder seiner Gruppe ohne Root hinzufügen und entfernen sowie das Gruppenpasswort ändern. `gpasswd` ist dafür als SUID-Programm installiert. Auf typischen Desktop-Systemen gibt es solche Gruppenverwalter selten.

## 2. Was macht der Befehl?

| Aufgabe | Aufruf | Wer darf das? |
| --- | --- | --- |
| Benutzer hinzufügen | `gpasswd -a BENUTZER GRUPPE` | Root oder Gruppenverwalter |
| Benutzer entfernen | `gpasswd -d BENUTZER GRUPPE` | Root oder Gruppenverwalter |
| Mitgliederliste ersetzen | `gpasswd -M a,b,c GRUPPE` | Root |
| Verwalter festlegen | `gpasswd -A a,b GRUPPE` | Root |
| Gruppenpasswort setzen | `gpasswd GRUPPE` | Root oder Gruppenverwalter |
| Gruppenpasswort entfernen | `gpasswd -r GRUPPE` | Root oder Gruppenverwalter |
| Zugang auf Mitglieder beschränken | `gpasswd -R GRUPPE` | Root oder Gruppenverwalter |

Die Aufgaben und Rechte folgen der [Debian-Manpage zu gpasswd](https://manpages.debian.org/trixie/passwd/gpasswd.1.en.html). Laut Manpage dürfen außer `-A` und `-M` keine Optionen kombiniert werden.

Eine neue Gruppenmitgliedschaft wirkt **nicht in laufenden Sitzungen**. Der Benutzer muss sich neu anmelden; für eine einzelne Shell hilft `newgrp`.

### Gruppenpasswörter

Ein Gruppenpasswort erlaubt Nichtmitgliedern, mit `newgrp GRUPPE` vorübergehend in die Gruppe zu wechseln. Die Manpage nennt Gruppenpasswörter ausdrücklich ein Sicherheitsproblem, weil mehrere Personen dasselbe Passwort kennen müssen. In der Praxis sind sie selten nötig.

### Grenzen

`gpasswd` bearbeitet nur die lokalen Dateien. Gruppen aus NIS, LDAP oder einem Verzeichnisdienst müssen dort geändert werden.

## 3. Syntax

```text
gpasswd [OPTION] GRUPPE
```

```bash
sudo gpasswd -a anna docker
sudo gpasswd -d anna docker
sudo gpasswd -M anna,ben projekt
```

Das bisherige NetMon-Beispiel `gpasswd --help` zeigt nur die Hilfe; der Platzhalter `gpasswd [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-a BENUTZER`, `--add BENUTZER` | Benutzer zur Gruppe hinzufügen. | Bestehende Mitglieder bleiben erhalten. |
| `-d BENUTZER`, `--delete BENUTZER` | Benutzer aus der Gruppe entfernen. | Entfernt nur Einträge der Mitgliederliste; die primäre Gruppe aus `/etc/passwd` bleibt unberührt. |
| `-M LISTE`, `--members LISTE` | Mitgliederliste **vollständig ersetzen**. | Nicht genannte Mitglieder fliegen heraus. |
| `-A LISTE`, `--administrators LISTE` | Gruppenverwalter festlegen. | Verwalter können ohne Root Mitglieder ändern. |
| `-r`, `--remove-password` | Gruppenpasswort leeren. | Danach können nur Mitglieder mit `newgrp` wechseln. |
| `-R`, `--restrict` | Gruppenpasswort auf `!` setzen. | Nur Mitglieder dürfen per `newgrp` wechseln. |
| `-Q VERZ`, `--root VERZ` | In einem anderen Wurzelverzeichnis arbeiten. | Nur absolute Pfade. |
| `--extrausers` | Zusätzliche Benutzerdatenbank verwenden. | Ubuntu-spezifisch; nicht in der Debian-Manpage. |
| `-h`, `--help` | Hilfe anzeigen. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Das Konto `anna` soll Mitglied der Gruppe `projekt` werden, ohne andere Mitglieder zu verändern. Das ändert die Gruppendatenbank und ist deshalb ein **Beispielszenario**; es wurde nicht ausgeführt.

### Schritt 1: Ausgangslage ansehen

```bash
getent group projekt
id -nG anna
```

Die erste Zeile zeigt die bisherigen Mitglieder, die zweite die Gruppen von `anna`.

### Schritt 2: Mitglied hinzufügen

```bash
sudo gpasswd -a anna projekt
```

Erwartete Ausgabe: `Adding user anna to group projekt`.

### Schritt 3: Ergebnis prüfen

```bash
getent group projekt
```

`anna` steht nun zusätzlich in der Mitgliederliste.

### Schritt 4: Wirkung herstellen

`anna` meldet sich ab und wieder an. Erst dann zeigt `id -nG` in ihrer Sitzung die neue Gruppe. Bis dahin kann sie in einer einzelnen Shell `newgrp projekt` verwenden.

### Rückgängig machen

```bash
sudo gpasswd -d anna projekt
```

Ausgabe: `Removing user anna from group projekt`.

## 6. Typische Anwendungsfälle

- **Zugriff auf Geräte oder Dienste geben:** etwa Gruppen wie `dialout` (serielle Schnittstellen) oder `lpadmin` (Druckerverwaltung).
- **Projektgruppen pflegen:** Mitglieder einzeln hinzufügen und entfernen.
- **Verwaltung delegieren:** Mit `-A` einer Teamleitung erlauben, Mitglieder ohne Root zu pflegen.
- **Mitgliedschaft entziehen:** `-d` ist gezielter als das Neuschreiben der Liste.

Im Vergleich zu `usermod -aG` arbeitet `gpasswd -a` aus Sicht der Gruppe. Das häufige Missgeschick von `usermod -G` ohne `-a` (alle anderen Zusatzgruppen werden entfernt) kann mit `gpasswd -a` nicht passieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Rechteausweitung über Gruppen

Manche Gruppen sind praktisch gleichbedeutend mit Root-Rechten. Auf dem geprüften System gibt es zum Beispiel `sudo` (Verwaltungsrechte über `sudo`) und `docker` (Zugriff auf den Docker-Dienst, der Container mit Root-Rechten startet). Auch `adm` (Lesen von Systemprotokollen) gibt Zugriff auf sensible Daten. Füge Konten solchen Gruppen nur bewusst hinzu.

### -M ersetzt die ganze Liste

Ein Tippfehler oder eine unvollständige Liste bei `-M` entfernt bestehende Mitglieder ohne Rückfrage.

### Gruppenpasswörter

Ein schwaches oder geteiltes Gruppenpasswort öffnet die Gruppe für jeden, der es kennt. Ohne zwingenden Grund keine Gruppenpasswörter setzen; vorhandene mit `-R` sperren.

### Verwalterrechte

Mit `-A` eingetragene Verwalter können beliebige vorhandene Konten in die Gruppe aufnehmen, auch ihr eigenes. Bei Gruppen mit Sonderrechten sollte es deshalb keine Gruppenverwalter geben.

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt bestehen. Die Root-Angabe wurde von „Nein/selten“ auf „erforderlich“ korrigiert, weil der Normalfall Verwaltungsrechte benötigt; die Ausnahme der Gruppenverwalter ist oben beschrieben.

## 8. Häufige Fehler

| Meldung | Ursache | Vorgehen |
| --- | --- | --- |
| `gpasswd: Permission denied.` | Weder Root noch Gruppenverwalter. | Mit Verwaltungsrechten arbeiten. |
| `gpasswd: user '...' does not exist` | Konto unbekannt. | `getent passwd NAME` prüfen. |
| `gpasswd: group '...' does not exist in /etc/group` | Gruppe unbekannt oder aus einem Verzeichnisdienst. | `getent group NAME`; ggf. Verzeichnisdienst nutzen. |
| `gpasswd: user '...' is not a member of '...'` | `-d` für ein Nichtmitglied. | Mitgliederliste prüfen. |
| Neue Gruppe wirkt nicht | Sitzung wurde vor der Änderung gestartet. | Neu anmelden oder `newgrp`. |
| Ohne Argumente nur Hilfe | Gruppe fehlt. | Gruppenname angeben (Rückgabewert war `2`). |

Die Meldungstexte wurden mit den englischen Meldungen im lokalen Programm abgeglichen; mit deutscher Spracheinstellung erscheinen Übersetzungen.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Einzeln mit `-a` und `-d` arbeiten** statt mit `-M`.
2. **Vorher und nachher `getent group GRUPPE` ausführen.**
3. **Bei Gruppen wie `sudo`, `docker`, `adm`, `disk` oder `shadow` besonders vorsichtig sein.**
4. **Keine Gruppenpasswörter setzen,** wenn es keinen klaren Grund gibt.
5. **Nach Änderungen neu anmelden lassen** und erst dann testen.

### Prüfstand

- **Geprüfte Version:** shadow 4.13 (Ubuntu-Paket `passwd`), Debian-Manpage aus shadow 4.17.4 zum Vergleich.
- **Tatsächlich ausgeführt:** `gpasswd --help`, `gpasswd` ohne Argumente (Rückgabe 2), Prüfung des SUID-Bits, Abgleich der Meldungstexte im Programm.
- **Nicht ausgeführt:** jede Änderung an Gruppen, Verwaltern oder Passwörtern, also auch das Beispiel aus Abschnitt 5; `-Q` und `--extrausers`.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `usermod -aG` | Fügt einen Benutzer aus Sicht des Kontos zu Zusatzgruppen hinzu. |
| `deluser BENUTZER GRUPPE` | Debian-Werkzeug zum Entfernen aus einer Gruppe. |
| `newgrp` | Wechselt in einer Shell in eine Gruppe, ggf. mit Gruppenpasswort. |
| `groupadd`, `groupdel`, `groupmod` | Legen Gruppen an, löschen oder ändern sie. |
| `getent group`, `id` | Zeigen Gruppen und Mitgliedschaften. |
| `grpck` | Prüft `/etc/group` und `/etc/gshadow` auf Konsistenz. |

Ausgangseintrag: Datensatz 110 in `index.json` (`gpasswd`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch die tatsächlichen Aufgaben, die Rechteregeln für Root und Gruppenverwalter, die Wirkung erst nach Neuanmeldung und die Risiken privilegierter Gruppen ersetzt. Die Root-Angabe wurde korrigiert.
