---
id: "groupdel"
name: "groupdel"
command: "groupdel"
category: "Benutzer & Rechte"
language: "de"
root_required: true
risk_level: "danger"
tags: ["benutzer", "gruppen", "kontenverwaltung", "shadow"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 112
reviewed_at: "2026-11-13"
locally_checked_version: "shadow 4.13 (Paket passwd 1:4.13+dfsg1-4ubuntu3.2); nur Hilfe und Meldungstexte"
---

# groupdel – Gruppe aus den Systemdateien löschen

## 1. Kurzbeschreibung

`groupdel` löscht eine Gruppe aus `/etc/group` und `/etc/gshadow`. Es ist das Basiswerkzeug der Shadow-Suite und auf praktisch allen Linux-Distributionen vorhanden. Unter Debian und Ubuntu ruft das komfortablere `delgroup` intern `groupdel` auf.

**Root-Rechte sind immer nötig**, weil die Gruppendateien nur Root schreiben darf.

## 2. Was macht der Befehl?

`groupdel GRUPPE` entfernt alle Einträge dieser Gruppe aus den Gruppendateien. Laut [Debian-Manpage zu groupdel](https://manpages.debian.org/trixie/passwd/groupdel.8.en.html) muss die Gruppe existieren, und die **primäre Gruppe eines vorhandenen Kontos** kann nicht gelöscht werden.

Nicht verändert werden:

- **Dateien** der Gruppe. Sie behalten die numerische GID. `ls -l` zeigt danach nur noch die Zahl.
- **Konten**, die Mitglied waren. Sie verlieren nur die Mitgliedschaft.
- **Laufende Prozesse**, die die Gruppe bereits in ihrer Gruppenliste haben. Sie behalten deren Rechte bis zum Ende.

Die Manpage verlangt ausdrücklich, alle Dateisysteme manuell auf verbliebene Dateien dieser Gruppe zu prüfen.

## 3. Syntax

```text
groupdel [OPTIONEN] GRUPPE
```

```bash
sudo groupdel altprojekt
```

Das bisherige NetMon-Beispiel `groupdel --help` zeigt nur die Hilfe; der Platzhalter `groupdel [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-f`, `--force` | Auch löschen, wenn die Gruppe primäre Gruppe eines Kontos ist. | Das Konto verweist danach auf eine nicht vorhandene GID. Nur in Ausnahmefällen. |
| `-R VERZ`, `--root VERZ` | In einem anderen Wurzelverzeichnis arbeiten (chroot). | Nur absolute Pfade. |
| `-P VERZ`, `--prefix VERZ` | Dateien unter einem Präfix bearbeiten, ohne chroot. | Für vorbereitete Systemabbilder. |
| `--extrausers` | Zusätzliche Benutzerdatenbank verwenden. | Ubuntu-spezifisch. |
| `-h`, `--help` | Hilfe anzeigen. | – |

`groupdel` hat bewusst keine Option „nur wenn leer“. Diese Prüfung bietet unter Debian `delgroup --only-if-empty`.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Die nicht mehr benötigte Gruppe `altprojekt` löschen, ohne verwaiste Dateien zu hinterlassen. Das verändert die Gruppendatenbank; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Gruppe, GID und Mitglieder feststellen

```bash
getent group altprojekt
```

Beispielausgabe: `altprojekt:x:1050:anna`. Merke dir die GID `1050`.

### Schritt 2: Prüfen, ob es eine primäre Gruppe ist

```bash
getent passwd | awk -F: '$4 == 1050 {print $1}'
```

Erscheint ein Kontoname, würde `groupdel` mit Rückgabewert `8` abbrechen. Das Konto braucht erst eine andere primäre Gruppe (`usermod -g`).

### Schritt 3: Dateien der Gruppe suchen und umstellen

```bash
sudo find / -xdev -gid 1050 -print 2>/dev/null
```

Für jedes weitere Dateisystem (etwa eine eigene `/home`-Partition) einzeln wiederholen. Gefundene Dateien mit `chgrp` einer passenden Gruppe zuordnen oder bewusst entfernen.

### Schritt 4: Sicherung und Löschen

```bash
sudo cp -a /etc/group /etc/gshadow /root/
sudo groupdel altprojekt
echo $?
```

Rückgabewert `0` bedeutet Erfolg. `groupdel` legt selbst ebenfalls Sicherungen `/etc/group-` und `/etc/gshadow-` an; diese werden aber bei der nächsten Änderung überschrieben.

### Schritt 5: Nachkontrolle

```bash
getent group altprojekt
sudo find / -xdev -nogroup -print 2>/dev/null | head
```

`getent` gibt nichts mehr aus. `-nogroup` findet Dateien, deren GID keiner Gruppe mehr zugeordnet ist.

## 6. Typische Anwendungsfälle

- **Aufräumen** nach Projektende oder nach Deinstallation eines Dienstes.
- **Reparatur:** Eine versehentlich angelegte Gruppe sofort wieder entfernen.
- **Systemabbilder vorbereiten** mit `-P` oder `-R`, ohne das laufende System zu verändern.

## 7. Risiken, Nebenwirkungen und Vorsicht

### GID-Wiederverwendung

Bleiben Dateien mit der alten GID liegen und wird die Nummer später neu vergeben, gehören diese Dateien automatisch der neuen Gruppe. Das kann vertrauliche Daten für fremde Personen öffnen.

### Systemgruppen

Gruppen wie `sudo`, `adm`, `shadow`, `audio`, `video`, `dialout`, `docker` oder Dienstgruppen werden von Programmen und Konfigurationen erwartet. Ihr Löschen kann Verwaltung, Geräte oder Dienste unbrauchbar machen.

### --force

Mit `-f` gelöschte Primärgruppen hinterlassen Konten mit einer GID ohne Namen. Neue Dateien dieser Konten erhalten dann eine „namenlose“ Gruppe.

### Keine Rückfrage

`groupdel` fragt nicht nach. Ein Tippfehler im Gruppennamen trifft eine andere vorhandene Gruppe.

Die ursprüngliche Einstufung „Rot – destruktiv/möglich kritisch“ bleibt bestehen. Die Root-Angabe wurde von „Häufig“ auf „erforderlich“ präzisiert.

## 8. Häufige Fehler

| Meldung oder Rückgabewert | Bedeutung | Vorgehen |
| --- | --- | --- |
| `groupdel: group '...' does not exist` (6) | Name falsch oder Gruppe aus einem Verzeichnisdienst. | `getent group` prüfen; Verzeichnisdienst nutzen. |
| `groupdel: cannot remove the primary group of user '...'` (8) | Primäre Gruppe eines Kontos. | Konto umstellen oder entfernen; `-f` nur bewusst. |
| Rückgabewert `10` | Gruppendatei konnte nicht geschrieben werden. | Sperrdateien, Platz und Rechte prüfen. |
| Rückgabewert `2` | Syntaxfehler. | `groupdel --help`. |
| `Permission denied` beziehungsweise Sperrfehler | Ohne Root aufgerufen. | Nur mit Verwaltungsrechten. |

Rückgabewerte laut Abschnitt EXIT VALUES der Debian-Manpage; Meldungstexte mit dem lokalen Programm abgeglichen, aber nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Unter Debian/Ubuntu `delgroup --only-if-empty` bevorzugen.**
2. **Erst Dateien suchen, dann löschen.**
3. **Gruppendateien vorher sichern.**
4. **Namen zweimal prüfen,** weil keine Rückfrage kommt.
5. **Kein `-f`,** außer der Zustand danach ist geplant.

### Prüfstand

- **Geprüfte Version:** shadow 4.13 (Ubuntu-Paket `passwd`); Debian-Manpage shadow 4.17.4.
- **Tatsächlich ausgeführt:** `groupdel --help`, Abgleich der Meldungstexte im Programm.
- **Nicht ausgeführt:** jede Löschung, auch an Kopierdateien. Nach dem Protokoll-Seiteneffekt bei `groupadd -P` wurde hier auf einen Präfix-Test verzichtet. Ungeprüft bleiben `-f`, `-R`, `-P`, `--extrausers` und alle Fehlerfälle.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `delgroup` | Debian-Werkzeug mit `--only-if-empty` und `--system`. |
| `groupadd`, `groupmod` | Gruppen anlegen und ändern. |
| `gpasswd -d`, `deluser BENUTZER GRUPPE` | Nur Mitgliedschaften entfernen. |
| `usermod -g` | Primäre Gruppe eines Kontos ändern. |
| `find -gid`, `find -nogroup` | Dateien einer GID beziehungsweise verwaiste Dateien finden. |
| `grpck` | Gruppendateien auf Konsistenz prüfen. |

Ausgangseintrag: Datensatz 112 in `index.json` (`groupdel`, Risiko „Rot – destruktiv/möglich kritisch“, Root „Häufig“). Der Hilfe-Platzhalter wurde durch die tatsächliche Wirkung, die Grenzen bei Primärgruppen und Dateien, die Rückgabewerte und einen vorsichtigen Ablauf ersetzt.
