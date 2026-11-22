---
id: "groupadd"
name: "groupadd"
command: "groupadd"
category: "Benutzer & Rechte"
language: "de"
root_required: true
risk_level: "caution"
tags: ["benutzer", "gruppen", "kontenverwaltung", "shadow"]
status: "Ausgearbeitet; Quellen geprüft; nur an eigenen Kopierdateien geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 111
reviewed_at: "2026-11-13"
locally_checked_version: "shadow 4.13 (Paket passwd 1:4.13+dfsg1-4ubuntu3.2)"
---

# groupadd – Neue Gruppe anlegen

## 1. Kurzbeschreibung

`groupadd` legt eine neue Gruppe an. Es trägt sie in `/etc/group` und `/etc/gshadow` ein und vergibt eine freie Gruppen-ID (GID). Das Werkzeug gehört zur Shadow-Suite und ist auf praktisch allen Linux-Distributionen vorhanden.

**Root-Rechte sind für das Anlegen einer Gruppe im laufenden System nötig.** Ohne Root kann `groupadd` die Systemdateien nicht sperren und nicht schreiben.

## 2. Was macht der Befehl?

`groupadd NAME` prüft den Namen, wählt eine GID und schreibt je eine Zeile in die Gruppendateien. Vorher legt es Sicherungskopien `/etc/group-` und `/etc/gshadow-` an. Die neue Gruppe hat zunächst keine Mitglieder und kein Passwort (`!` in `/etc/gshadow`).

Ohne `-g` wählt `groupadd` die kleinste GID, die mindestens `GID_MIN` ist und größer als alle vorhandenen GIDs in diesem Bereich. Auf dem geprüften System gilt `GID_MIN 1000` und `GID_MAX 60000` laut `/etc/login.defs`. Mit `-r` wird eine Systemgruppe aus dem Bereich `SYS_GID_MIN` bis `SYS_GID_MAX` angelegt; diese Werte sind lokal auskommentiert (Vorgabe im Kommentar: 100 bis 999).

Die Beschreibung folgt der [Debian-Manpage zu groupadd](https://manpages.debian.org/trixie/passwd/groupadd.8.en.html) und der lokalen Manpage von shadow 4.13.

### Erlaubte Namen

Die allgemeine Shadow-Regel lautet: Buchstaben, Ziffern, Unterstrich und Bindestrich, optional ein `$` am Ende, kein Bindestrich am Anfang, nicht nur Ziffern, höchstens 32 Zeichen. **Debian und Ubuntu lockern diese Regel:** Laut lokaler Manpage sind dort nur ein führendes `-`, `+` oder `~` sowie Doppelpunkt, Komma und Leerraum verboten; Ubuntu verbietet zusätzlich rein numerische Namen. Für übertragbare Skripte empfiehlt sich trotzdem die strenge allgemeine Regel mit Kleinbuchstaben.

### Debian-Alternative

Unter Debian und Ubuntu gibt es zusätzlich `addgroup` aus dem Paket adduser. Es ruft `groupadd` auf und wendet die Regeln aus `/etc/adduser.conf` an.

## 3. Syntax

```text
groupadd [OPTIONEN] GRUPPE
```

```bash
sudo groupadd projekt
sudo groupadd -g 1600 projekt
sudo groupadd -r dienstgruppe
```

Das bisherige NetMon-Beispiel `groupadd --help` zeigt nur die Hilfe; der Platzhalter `groupadd [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-g GID`, `--gid GID` | Bestimmte GID verwenden. | Muss frei sein, außer mit `-o`. |
| `-r`, `--system` | Systemgruppe anlegen. | GID aus dem Systembereich; für Dienste. |
| `-f`, `--force` | Erfolg melden, wenn die Gruppe schon existiert. | Ist die GID aus `-g` belegt, wird eine andere gewählt. |
| `-o`, `--non-unique` | Doppelte GID zulassen. | Zwei Namen für dieselbe GID; selten sinnvoll. |
| `-U LISTE`, `--users LISTE` | Mitglieder gleich mit eintragen. | Kommagetrennte Kontonamen. |
| `-K SCHLÜSSEL=WERT` | Vorgaben aus `login.defs` überschreiben. | Zum Beispiel `-K GID_MIN=2000`. |
| `-p HASH`, `--password HASH` | Verschlüsseltes Gruppenpasswort setzen. | Laut Manpage nicht empfohlen: in der Prozessliste sichtbar. |
| `-R VERZ`, `--root VERZ` | In einem anderen Wurzelverzeichnis arbeiten (chroot). | Nur absolute Pfade. |
| `-P VERZ`, `--prefix VERZ` | Dateien unter einem Präfix bearbeiten, ohne chroot. | Für vorbereitete Systemabbilder. |
| `--extrausers` | Zusätzliche Benutzerdatenbank verwenden. | Ubuntu-spezifisch. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Eine Projektgruppe `projekt` anlegen und `anna` aufnehmen. Das verändert die Gruppendatenbank und ist für das laufende System ein **Beispielszenario**; es wurde dort nicht ausgeführt.

### Schritt 1: Prüfen, ob Name oder GID belegt sind

```bash
getent group projekt
getent group 1600
```

Keine Ausgabe bedeutet: frei. `getent` fragt auch LDAP oder andere konfigurierte Quellen ab; `groupadd` verweigert Namen, die dort schon existieren.

### Schritt 2: Gruppe anlegen

```bash
sudo groupadd -g 1600 projekt
echo $?
```

Rückgabewert `0` bedeutet Erfolg. Ohne `-g` wählt `groupadd` die GID selbst; für Gruppen, die auf mehreren Rechnern gleich sein sollen, ist eine feste GID sinnvoll.

### Schritt 3: Kontrollieren und Mitglied aufnehmen

```bash
getent group projekt
sudo gpasswd -a anna projekt
```

Erwartet wird zuerst `projekt:x:1600:`. Danach steht `anna` in der Mitgliederliste.

### Tatsächlich geprüfte Variante an eigenen Dateien

Mit `-P` lässt sich `groupadd` auf Kopien der Kontodateien in einem eigenen Ordner anwenden. Im Test lag unter `PRÄFIX/etc/` eine selbst erstellte Minimalfassung von `passwd`, `shadow`, `group`, `gshadow` sowie eine Kopie von `login.defs`:

```bash
groupadd -P "$PWD/praefix" testgruppe
cat praefix/etc/group
```

Der Aufruf lief ohne Root-Rechte, Rückgabewert `0`. Die Datei enthielt danach `testgruppe:x:1501:` – die nächste freie GID nach der vorhandenen 1500 –, und es entstanden Sicherungen `group-` und `gshadow-`.

**Wichtige Beobachtung:** Auch mit `-P` schrieb `groupadd` Einträge ins **echte Systemprotokoll** (Journal und `/var/log/auth.log`), darunter die Zeile `new group: name=testgruppe, GID=1501` ohne Pfadangabe. Eine echte Gruppe entstand nicht. Wer Protokolle überwacht, sollte solche Übungen deshalb ankündigen oder unterlassen.

## 6. Typische Anwendungsfälle

- **Projekt- oder Abteilungsgruppen** für gemeinsame Ordner anlegen.
- **Dienstgruppen** mit `-r` für Programme, die Zugriff auf bestimmte Dateien oder Geräte brauchen.
- **Gleiche GIDs auf mehreren Rechnern,** etwa für NFS-Freigaben, mit `-g`.
- **Idempotente Skripte:** `groupadd -f NAME` meldet auch bei vorhandener Gruppe Erfolg.

## 7. Risiken, Nebenwirkungen und Vorsicht

Das Anlegen einer leeren Gruppe löscht keine Daten. Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt trotzdem passend:

- **Übernahme alter Dateien:** Wird eine GID wiederverwendet, die früher eine gelöschte Gruppe hatte, gehören deren verbliebene Dateien sofort der neuen Gruppe. Vorher mit `sudo find / -xdev -gid GID` prüfen.
- **Doppelte GIDs mit `-o`:** Zwei Gruppennamen teilen sich dieselben Rechte. Das erschwert Prüfungen und kann ungewollten Zugriff geben.
- **Passwort mit `-p`:** Der übergebene Hash ist in der Prozessliste sichtbar.
- **Namenskollisionen:** Ein Name, der in einem Verzeichnisdienst oder auf anderen Rechnern eine andere GID hat, führt zu verwirrenden Rechten.
- **Protokolleinträge:** Jede Ausführung erzeugt Einträge im Systemprotokoll, wie im Test beobachtet.

## 8. Häufige Fehler

| Meldung oder Rückgabewert | Bedeutung | Vorgehen |
| --- | --- | --- |
| `groupadd: Permission denied.` oder `groupadd: cannot lock /etc/group; try again later.` | Ohne Root-Rechte am laufenden System. | Mit Verwaltungsrechten ausführen. |
| `groupadd: group '...' already exists` (9) | Name vergeben. | Anderen Namen wählen oder `-f` in Skripten. |
| `groupadd: GID '...' already exists` (4) | GID vergeben. | Andere GID wählen; `-o` nur bewusst. |
| `groupadd: '...' is not a valid group name` (3) | Name verstößt gegen die Regeln. | Kleinbuchstaben, Ziffern, `_`, `-` verwenden. |
| Rückgabewert `2` | Syntaxfehler in der Befehlszeile. | `groupadd --help` lesen. |
| Rückgabewert `10` | Gruppendatei konnte nicht aktualisiert werden. | Platz, Sperrdateien und Rechte prüfen. |

Die Rückgabewerte stammen aus dem Abschnitt EXIT VALUES der Debian-Manpage. Die Meldungstexte wurden mit den englischen Meldungen im lokalen Programm abgeglichen, aber nicht einzeln praktisch ausgelöst. Bei fehlenden Rechten kann statt `Permission denied.` auch `cannot lock /etc/group; try again later.` erscheinen.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Vorher mit `getent group` prüfen,** ob Name und GID frei sind.
2. **Kleinbuchstaben ohne Sonderzeichen** verwenden.
3. **Feste GIDs nur, wenn nötig,** dann aber dokumentieren.
4. **Kein `-o` und kein `-p`** im normalen Betrieb.
5. **Nach dem Anlegen mit `getent group NAME` kontrollieren.**

### Prüfstand

- **Geprüfte Version:** shadow 4.13 (Ubuntu-Paket `passwd`).
- **Tatsächlich ausgeführt:** `groupadd --help`; ein Lauf mit `-P` auf selbst erstellten Minimal-Kontodateien in einem eigenen temporären Ordner (GID-Wahl 1501, Sicherungsdateien, Rückgabe 0). Dabei entstanden drei Einträge im echten Systemprotokoll; eine echte Gruppe wurde nicht angelegt (mit `getent` bestätigt).
- **Nicht ausgeführt:** Anlegen einer Gruppe im laufenden System, `-g`, `-r`, `-f`, `-o`, `-U`, `-K`, Fehlerfälle und Rückgabewerte außer 0.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `addgroup` | Debian-Werkzeug mit Regeln aus `/etc/adduser.conf`. |
| `groupmod` | Ändert Name oder GID einer Gruppe. |
| `groupdel`, `delgroup` | Entfernen Gruppen. |
| `gpasswd`, `usermod -aG` | Fügen Mitglieder hinzu. |
| `getent group` | Prüft vorhandene Gruppen in allen Quellen. |
| `grpck` | Prüft die Gruppendateien auf Konsistenz. |

Ausgangseintrag: Datensatz 111 in `index.json` (`groupadd`, Risiko „Gelb – Admin/Vorsicht“, Root „Häufig“). Die Root-Angabe wurde auf „erforderlich“ präzisiert. Der Hilfe-Platzhalter wurde durch GID-Vergabe, Namensregeln mit Debian-/Ubuntu-Besonderheiten, Optionen, Rückgabewerte und einen beobachteten Protokoll-Seiteneffekt ersetzt.
