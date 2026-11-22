---
id: "groupmod"
name: "groupmod"
command: "groupmod"
category: "Benutzer & Rechte"
language: "de"
root_required: true
risk_level: "caution"
tags: ["benutzer", "gruppen", "kontenverwaltung", "shadow"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 113
reviewed_at: "2026-11-13"
locally_checked_version: "shadow 4.13 (Paket passwd 1:4.13+dfsg1-4ubuntu3.2); nur Hilfe und Meldungstexte"
---

# groupmod – Name, GID oder Mitglieder einer Gruppe ändern

## 1. Kurzbeschreibung

`groupmod` ändert eine vorhandene Gruppe in `/etc/group` und `/etc/gshadow`: ihren **Namen**, ihre **Gruppen-ID (GID)**, ihr Passwort oder ihre Mitgliederliste. Es gehört zur Shadow-Suite und ist auf praktisch allen Linux-Distributionen vorhanden.

**Root-Rechte sind nötig**, weil die Gruppendateien nur Root schreiben darf.

## 2. Was macht der Befehl?

| Änderung | Aufruf | Was zusätzlich passiert |
| --- | --- | --- |
| Umbenennen | `groupmod -n NEU ALT` | GID bleibt; Dateien behalten ihre Zuordnung. |
| GID ändern | `groupmod -g GID GRUPPE` | Konten mit dieser Primärgruppe werden angepasst; **Dateien nicht**. |
| Mitglieder setzen | `groupmod -U a,b GRUPPE` | Ohne `-a` wird die Liste ersetzt. |
| Mitglieder ergänzen | `groupmod -a -U c GRUPPE` | Vorhandene Mitglieder bleiben. |
| Passwort setzen | `groupmod -p HASH GRUPPE` | Hash in der Prozessliste sichtbar; nicht empfohlen. |

Laut [Debian-Manpage zu groupmod](https://manpages.debian.org/trixie/passwd/groupmod.8.en.html) müssen Dateien mit der alten GID, die weiter zur Gruppe gehören sollen, **manuell** umgestellt werden. Bei `-g` prüft `groupmod` außerdem nicht, ob die neue GID in den Bereichen aus `/etc/login.defs` liegt.

### Namensänderung und Konfigurationen

Viele Konfigurationen verweisen auf Gruppen **per Name**, etwa `%gruppe` in den sudo-Regeln, Freigaben in Samba oder Regeln von Diensten. Nach einer Umbenennung greifen diese Verweise ins Leere. Dateien selbst speichern dagegen nur die GID und sind von einer Umbenennung nicht betroffen.

## 3. Syntax

```text
groupmod [OPTIONEN] GRUPPE
```

```bash
sudo groupmod -n entwicklung projekt
sudo groupmod -g 1600 entwicklung
sudo groupmod -a -U anna,ben entwicklung
```

Das bisherige NetMon-Beispiel `groupmod --help` zeigt nur die Hilfe; der Platzhalter `groupmod [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-n NEU`, `--new-name NEU` | Gruppe umbenennen. | Verweise per Namen anpassen. |
| `-g GID`, `--gid GID` | Neue GID setzen. | Dateien danach selbst umstellen. |
| `-o`, `--non-unique` | Mit `-g` eine bereits benutzte GID zulassen. | Zwei Gruppen teilen sich dann alle Rechte. |
| `-U LISTE`, `--users LISTE` | Mitgliederliste setzen. | Ersetzt die Liste, außer mit `-a`. |
| `-a`, `--append` | Mit `-U` Mitglieder ergänzen. | Sicherere Wahl für Ergänzungen. |
| `-p HASH`, `--password HASH` | Verschlüsseltes Gruppenpasswort setzen. | Nicht empfohlen; besser `gpasswd`. |
| `-R VERZ`, `--root VERZ` | In einem anderen Wurzelverzeichnis arbeiten. | Nur absolute Pfade. |
| `-P VERZ`, `--prefix VERZ` | Dateien unter einem Präfix bearbeiten. | Ohne chroot. |
| `-h`, `--help` | Hilfe anzeigen. | – |

**Versionshinweis:** `-a` und `-U` sind in der lokalen Hilfe von shadow 4.13 und in der Debian-Manpage (4.17.4) enthalten. **Prüfpunkt:** Ältere Shadow-Versionen kennen sie möglicherweise nicht; vorher `groupmod --help` prüfen.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Die Gruppe `projekt` (GID 1050) soll künftig `entwicklung` heißen und auf allen Rechnern die GID 1600 haben. Das verändert die Gruppendatenbank und Dateien; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Ausgangslage und Belegung prüfen

```bash
getent group projekt
getent group entwicklung
getent group 1600
```

Die erste Zeile zeigt die bisherige GID. Die beiden anderen Abfragen dürfen nichts ausgeben, sonst sind Name oder GID belegt.

### Schritt 2: Sicherung

```bash
sudo cp -a /etc/group /etc/gshadow /root/
```

### Schritt 3: Umbenennen

```bash
sudo groupmod -n entwicklung projekt
```

Dateien zeigen nun automatisch `entwicklung`, weil sie nur die GID speichern.

### Schritt 4: GID ändern und Dateien nachziehen

```bash
sudo groupmod -g 1600 entwicklung
sudo find / -xdev -gid 1050 -exec chgrp -h entwicklung {} +
```

Die zweite Zeile sucht Dateien mit der **alten** GID und ordnet sie der Gruppe neu zu. `-h` ändert symbolische Links selbst statt ihrer Ziele. Weitere Dateisysteme einzeln bearbeiten.

### Schritt 5: Verweise per Name anpassen

```bash
sudo grep -rn 'projekt' /etc/sudoers /etc/sudoers.d 2>/dev/null
```

Gefundene Regeln mit `visudo` anpassen. Andere Dienste haben eigene Konfigurationsorte.

## 6. Typische Anwendungsfälle

- **GIDs zwischen Rechnern angleichen,** damit gemeinsame Laufwerke (NFS) die richtigen Rechte zeigen.
- **Gruppen umbenennen** nach Umstrukturierung.
- **Mitgliederliste ergänzen** in einem Schritt mit `-a -U`.
- **Konflikte beheben,** wenn eine Paketinstallation eine GID belegt, die anderswo schon vergeben ist.

## 7. Risiken, Nebenwirkungen und Vorsicht

- **Zugriffsverlust nach `-g`:** Dateien mit der alten GID gehören danach keiner Gruppe mehr. Gruppenmitglieder verlieren den Zugriff, bis die Dateien umgestellt sind. Wird die alte GID später neu vergeben, erhält eine fremde Gruppe Zugriff.
- **Laufende Prozesse:** Prozesse und angemeldete Benutzer behalten bis zur Neuanmeldung die alte GID in ihrer Gruppenliste.
- **Verweise per Name nach `-n`:** sudo-Regeln, Dienstkonfigurationen und Skripte, die den alten Namen verwenden, wirken nicht mehr – ggf. werden dadurch Rechte entzogen oder Dienste starten nicht.
- **`-U` ohne `-a`:** Ersetzt die komplette Mitgliederliste; nicht genannte Mitglieder verlieren den Zugang.
- **`-o`:** Doppelte GIDs erschweren Prüfungen und verwischen Rechtegrenzen.
- **Systemgruppen:** Name oder GID von Gruppen wie `sudo`, `adm` oder Dienstgruppen nicht ändern; Pakete erwarten sie.

Die ursprüngliche Einstufung „Gelb – Admin/Vorsicht“ bleibt bestehen. Die Root-Angabe wurde von „Häufig“ auf „erforderlich“ präzisiert.

## 8. Häufige Fehler

| Meldung oder Rückgabewert | Bedeutung | Vorgehen |
| --- | --- | --- |
| `groupmod: group '...' does not exist` (6) | Gruppe unbekannt. | `getent group` prüfen. |
| `groupmod: group '...' already exists` (9) | Neuer Name vergeben. | Anderen Namen wählen. |
| `groupmod: GID '...' already exists` (4) | Neue GID vergeben. | Andere GID; `-o` nur bewusst. |
| `groupmod: invalid group name '...'` (3) | Name verstößt gegen Regeln. | Kleinbuchstaben, Ziffern, `_`, `-`. |
| `groupmod: group '...' does not exist in /etc/group` | Gruppe stammt aus einem Verzeichnisdienst. | Dort ändern. |
| Rückgabewert `10` | Gruppendatei nicht schreibbar. | Sperren, Platz, Rechte prüfen. |

Rückgabewerte laut Debian-Manpage, Meldungstexte mit dem lokalen Programm abgeglichen; nichts davon wurde praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Vorher sichern** und Belegung von Name und GID prüfen.
2. **Umbenennen ist harmloser als GID-Wechsel,** weil Dateien unberührt bleiben.
3. **Nach `-g` sofort die alten Dateien nachziehen** (`find -gid ALT`).
4. **Mitglieder immer mit `-a -U` ergänzen** oder `gpasswd -a` verwenden.
5. **Betroffene Benutzer neu anmelden lassen.**

### Prüfstand

- **Geprüfte Version:** shadow 4.13 (Ubuntu-Paket `passwd`); Debian-Manpage shadow 4.17.4.
- **Tatsächlich ausgeführt:** `groupmod --help`, Abgleich der Meldungstexte im Programm.
- **Nicht ausgeführt:** jede Gruppenänderung, auch an Kopierdateien (wegen des bei `groupadd -P` beobachteten Protokoll-Seiteneffekts); alle Optionen und Fehlerfälle.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `groupadd`, `groupdel` | Gruppen anlegen und löschen. |
| `gpasswd` | Mitglieder, Verwalter und Passwort verwalten. |
| `usermod -g`, `usermod -aG` | Gruppen aus Sicht eines Kontos ändern. |
| `chgrp`, `find -gid` | Dateien nach GID-Wechsel nachziehen. |
| `visudo` | sudo-Regeln mit Gruppennamen anpassen. |
| `grpck` | Gruppendateien prüfen. |

Ausgangseintrag: Datensatz 113 in `index.json` (`groupmod`, Risiko „Gelb – Admin/Vorsicht“, Root „Häufig“). Der Hilfe-Platzhalter wurde durch die konkreten Änderungsarten, die Folgen für Dateien und Verweise per Namen, die Rückgabewerte und einen vollständigen Ablauf ersetzt.
