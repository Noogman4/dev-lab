---
id: "getfacl"
name: "getfacl"
command: "getfacl"
category: "Benutzer & Rechte"
language: "de"
root_required: false
risk_level: "safe"
tags: ["benutzer", "rechte", "acl", "dateirechte"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 109
reviewed_at: "2026-11-13"
locally_checked_version: "acl 2.3.2 (getfacl 2.3.2)"
---

# getfacl – Zugriffssteuerungslisten (ACLs) von Dateien anzeigen

## 1. Kurzbeschreibung

`getfacl` zeigt die **Access Control List (ACL)** einer Datei oder eines Ordners. Eine ACL erweitert die klassischen Rechte (Eigentümer, Gruppe, andere) um Einträge für weitere benannte Benutzer und Gruppen, zum Beispiel „Benutzer `anna` darf lesen“.

**Root-Rechte sind nicht nötig.** Wer einen Ordner lesen darf, darf auch die ACLs der darin enthaltenen Dateien lesen. `getfacl` verändert nichts.

## 2. Was macht der Befehl?

`getfacl` gibt für jede Datei einen Textblock aus:

```text
# file: projekt/plan.txt
# owner: happy
# group: happy
user::rw-
user:nobody:rw-	#effective:r--
group::rw-	#effective:r--
mask::r--
other::---
```

| Zeile | Bedeutung |
| --- | --- |
| `# file`, `# owner`, `# group` | Kopfzeilen: Pfad, Eigentümer, Besitzergruppe. |
| `# flags: -s-` | Nur wenn setuid, setgid oder Sticky gesetzt ist. |
| `user::` | Rechte des Eigentümers. |
| `user:NAME:` | Rechte eines benannten Benutzers. |
| `group::` | Rechte der Besitzergruppe. |
| `group:NAME:` | Rechte einer benannten Gruppe. |
| `mask::` | Obergrenze für benannte Benutzer, benannte Gruppen und die Besitzergruppe. |
| `other::` | Rechte aller anderen. |
| `default:...` | Vorgabe-ACL eines Ordners für neu angelegte Einträge. |

Der Kommentar `#effective:` erscheint, wenn die Maske einen Eintrag einschränkt. Im Beispiel steht für `nobody` zwar `rw-`, wirksam ist aber nur `r--`.

Die Beschreibung folgt der [Debian-Manpage zu getfacl](https://manpages.debian.org/trixie/acl/getfacl.1.en.html), die das Ausgabeformat Zeile für Zeile erklärt. Die Ausgabe kann direkt als Eingabe für `setfacl --restore` dienen.

### ACLs erkennen

In `ls -l` zeigt ein `+` hinter den Rechten, dass eine erweiterte ACL vorhanden ist: `-rw-rw----+`. **Wichtig:** Bei Dateien mit erweiterter ACL zeigen die mittleren drei Zeichen in `ls -l` die **Maske**, nicht die Rechte der Besitzergruppe. Im Test führte `chmod g-w` deshalb zu `mask::r--`, während `group::rw-` gespeichert blieb.

## 3. Syntax

```text
getfacl [OPTIONEN] DATEI ...
getfacl [OPTIONEN] -
```

- Mehrere Dateien werden durch Leerzeilen getrennt ausgegeben.
- Ein einzelnes `-` liest die Dateinamen von der Standardeingabe.

```bash
getfacl bericht.txt
getfacl -R -s projekt
getfacl -R projekt > acl-sicherung.txt
```

Das bisherige NetMon-Beispiel `getfacl --help` funktioniert und zeigt die Optionen; der Platzhalter `getfacl [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-a`, `--access` | Nur die Zugriffs-ACL anzeigen. | Ohne `default:`-Zeilen. |
| `-d`, `--default` | Nur die Vorgabe-ACL anzeigen. | Nur Ordner haben eine. |
| `-c`, `--omit-header` | Kopfzeilen weglassen. | Praktisch zum Vergleichen. |
| `-e`, `--all-effective` | `#effective` immer anzeigen. | Auch wenn gleich. |
| `-E`, `--no-effective` | `#effective` nie anzeigen. | Achtung: verbirgt die Maskenwirkung. |
| `-s`, `--skip-base` | Dateien ohne erweiterte Einträge überspringen. | Findet mit `-R` alle Dateien mit ACL. |
| `-R`, `--recursive` | Ordner rekursiv durchlaufen. | Symbolischen Links in Unterordnern wird standardmäßig nicht gefolgt. |
| `-L`, `-P` | Links folgen beziehungsweise nicht folgen. | Nur mit `-R` wirksam. |
| `-t`, `--tabular` | Tabellarische Ausgabe. | Durch die Maske unwirksame Rechte erscheinen als Großbuchstaben. |
| `-n`, `--numeric` | Numerische IDs statt Namen. | Für Sicherungen zwischen Systemen. |
| `-p`, `--absolute-names` | Führenden `/` nicht entfernen. | Ohne `-p` meldet `getfacl` `Removing leading '/' from absolute path names`. |
| `--one-file-system` | Andere Dateisysteme überspringen. | In der lokalen Hilfe, nicht in der Manpage. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Eine ACL an einer eigenen Übungsdatei sichtbar machen und die Wirkung der Maske verstehen.

### Schritt 1: Übungsdatei anlegen und ACL lesen

```bash
uebung="$(mktemp -d -t netmon-getfacl-XXXXXX)" || exit 1
cd "$uebung" || exit 1
mkdir projekt
printf 'x\n' > projekt/plan.txt
getfacl projekt/plan.txt
```

Ohne erweiterte Einträge zeigt `getfacl` nur `user::`, `group::` und `other::` – also die klassischen Rechte.

### Schritt 2: Testweise einen ACL-Eintrag setzen

```bash
setfacl -m u:nobody:rw projekt/plan.txt
ls -l projekt/plan.txt
getfacl projekt/plan.txt
```

`setfacl` ergänzt einen Eintrag für das Systemkonto `nobody` an deiner eigenen Datei. `ls -l` zeigt nun ein `+`. `getfacl` listet `user:nobody:rw-` und eine automatisch angelegte Maske `mask::rw-`.

### Schritt 3: Maskenwirkung sehen

```bash
chmod g-w projekt/plan.txt
getfacl projekt/plan.txt
getfacl -t projekt/plan.txt
```

`chmod g-w` verändert bei erweiterter ACL die Maske. Danach steht hinter `user:nobody:rw-` der Kommentar `#effective:r--`. Die Tabellenform zeigt das verhinderte Schreibrecht als großes `W`.

### Schritt 4: Alle Dateien mit ACL finden

```bash
getfacl -R -s projekt
```

Nur `projekt/plan.txt` erscheint, weil der Ordner selbst keine erweiterten Einträge hat.

## 6. Typische Anwendungsfälle

- **Fehlersuche bei Zugriffsproblemen:** Wenn `ls -l` scheinbar ausreichende Rechte zeigt, kann eine ACL-Maske oder ein benannter Eintrag die Ursache sein.
- **Rechte sichern:** `getfacl -R ordner > acl.txt` speichert Rechte und ACLs vor einer Änderung. Wiederherstellen mit `setfacl --restore=acl.txt`.
- **Prüfung von Freigaben:** `getfacl -R -s /srv/freigabe` zeigt alle Dateien mit zusätzlichen Berechtigungen.
- **Vorgabe-ACL prüfen:** `getfacl -d ordner` zeigt, welche Rechte neue Dateien automatisch erhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

`getfacl` ist rein lesend. Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ wurde auf `safe` gesenkt.

Zu beachten:

- **Offenlegung:** Die Ausgabe nennt Konten- und Gruppennamen sowie Pfade. Eine gespeicherte Sicherung mit `-R` kann Rückschlüsse auf vertrauliche Ordnerstrukturen erlauben.
- **Pfade in Sicherungen:** Ohne `-p` sind Pfade relativ gespeichert. Eine Wiederherstellung muss im passenden Arbeitsordner erfolgen.
- **Namen und Nummern:** Ohne `-n` werden Namen gespeichert. Auf einem anderen System können dieselben Namen andere IDs haben – oder fehlen.
- **Dateisysteme ohne ACL:** Dort zeigt `getfacl` nur die klassischen Rechte. Das heißt nicht, dass dort niemand Zusatzrechte hat; manche Netzdateisysteme nutzen eigene Rechtemodelle (etwa NFSv4-ACLs). **Prüfpunkt** für Netzlaufwerke.
- **Laufzeit:** `-R` über große Bäume erzeugt viel Ausgabe und Last.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `getfacl: Removing leading '/' from absolute path names` | Hinweis, kein Fehler. | Mit `-p` absolute Pfade behalten. |
| `getfacl: ...: No such file or directory` | Pfad falsch. | Arbeitsordner und Schreibweise prüfen. |
| `getfacl: ...: Permission denied` | Ordner auf dem Weg nicht lesbar beziehungsweise nicht betretbar. | Mit `namei -l PFAD` die Stelle finden. |
| Benannter Benutzer hat trotz `rw-` kein Schreibrecht | Maske schränkt ein (`#effective:r--`). | Maske mit `setfacl -m m::rw` anpassen, wenn das gewollt ist. |
| `getfacl: command not found` | Paket `acl` fehlt. | Paket installieren lassen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **`getfacl` gefahrlos ausprobieren;** es ändert nichts.
2. **Auf das `+` in `ls -l` achten** und dann `getfacl` verwenden.
3. **`#effective` ernst nehmen;** die wirksamen Rechte stehen dort.
4. **Vor Änderungen mit `setfacl` oder `chmod -R` eine Sicherung anlegen:** `getfacl -R ordner > acl.txt`.
5. **Für Prüfungen zwischen Systemen `-n` nutzen.**

### Prüfstand

- **Geprüfte Version:** getfacl 2.3.2 (Paket acl 2.3.2-1build1.1) auf ext4.
- **Tatsächlich ausgeführt** im Testordner: Anzeige ohne und mit benanntem Eintrag, `+` in `ls -l`, Maskenwirkung nach `chmod g-w`, `-c`, `-E`, `-t` (Großbuchstaben), `-s -R`, `-p` und Hinweis zum führenden `/`, Vorgabe-ACL eines Ordners und deren Vererbung, Sicherung mit `-R` und Wiederherstellung über `setfacl --restore`.
- **Nicht geprüft:** `-L`/`-P`, `-n` zwischen verschiedenen Systemen, Netzdateisysteme, `POSIXLY_CORRECT`.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `setfacl` | Setzt, ändert und entfernt ACL-Einträge; stellt Sicherungen wieder her. |
| `chmod` | Ändert klassische Rechte; bei erweiterter ACL die Maske. |
| `ls -l` | Zeigt mit `+`, dass eine ACL vorhanden ist. |
| `namei -l` | Zeigt Rechte entlang eines Pfads. |
| `cp -a`, `rsync -A`, `tar --acls` | Übernehmen ACLs beim Kopieren oder Archivieren, sofern unterstützt. |

Ausgangseintrag: Datensatz 109 in `index.json` (`getfacl`, Risiko „Gelb – Admin/Vorsicht“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch das Ausgabeformat, die Maskenwirkung, Sicherungsnutzung und einen geprüften Ablauf ersetzt. Die Risikostufe wurde auf „sicher lesend“ gesenkt.
