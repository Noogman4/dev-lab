---
id: "sshfs"
name: "sshfs"
command: "sshfs"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "ssh", "fuse", "einhaengen"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 173
reviewed_at: "2026-11-13"
locally_checked_version: "SSHFS 3.7.3, FUSE 3.14.0; nur Version"
---

# sshfs – Entfernte Ordner per SSH als lokales Dateisystem einhängen

## 1. Kurzbeschreibung

`sshfs` hängt einen Ordner eines anderen Rechners so ein, als läge er lokal. Laut [Debian-Manpage zu sshfs](https://manpages.debian.org/trixie/sshfs/sshfs.1.en.html) nutzt es dazu das **SFTP-Subsystem** von SSH; auf dem Server ist meist nichts weiter einzurichten. Lokal arbeitet `sshfs` über **FUSE** (Dateisysteme im Benutzerbereich).

**Root-Rechte sind nicht nötig – die Manpage empfiehlt ausdrücklich, `sshfs` als normaler Benutzer zu starten.** Der Einhängepunkt muss dir gehören. Rechte auf dem Server richten sich nach dem dort verwendeten Konto.

## 2. Was macht der Befehl?

`sshfs BENUTZER@HOST:ORDNER EINHÄNGEPUNKT` baut eine SSH-Verbindung auf und stellt den entfernten Ordner unter dem lokalen Einhängepunkt bereit. Ohne Ordnerangabe wird das Heimatverzeichnis eingehängt. Programme lesen und schreiben dort, als wären es lokale Dateien; jede Aktion wird über SSH ausgeführt.

Wichtige Vorgaben laut Manpage:

- **Rechte:** Lokale Rechteprüfungen sind standardmäßig aus. Jeder, der auf den Einhängepunkt zugreifen kann, darf alles, was das Serverkonto darf; mit `-o default_permissions` prüft der Kernel lokal.
- **Zugriff:** Standardmäßig hat **nur das einhängende Konto** Zugriff; `-o allow_other` öffnet ihn für andere.
- **IDs:** Benutzer- und Gruppennummern werden standardmäßig nicht übersetzt (`idmap=none`); mit `-o idmap=user` erscheinen Dateien des Serverkontos als deine.
- **Keine Zeitlimits:** Bricht die Verbindung ab, blockieren Zugriffe, bis die Verbindung zurückkehrt oder getrennt wird.

Aushängen unter Linux: `fusermount3 -u EINHÄNGEPUNKT`.

## 3. Syntax

```text
sshfs [BENUTZER@]HOST:[ORDNER] EINHÄNGEPUNKT [OPTIONEN]
fusermount3 -u EINHÄNGEPUNKT
```

```bash
mkdir -p ~/mnt/server
sshfs anna@server.example.org:/srv/daten ~/mnt/server -o idmap=user,reconnect,ServerAliveInterval=15
fusermount3 -u ~/mnt/server
```

Das bisherige NetMon-Beispiel `sshfs --help` ist gültig (`-h`, `--help` laut Manpage). Der Platzhalter `sshfs [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-p PORT` | SSH-Port. | Entspricht `-o port=PORT`. |
| `-o idmap=user` | Serverkonto-IDs auf eigenes Konto abbilden. | Vorgabe `none`. |
| `-o reconnect` | Nach Abbruch neu verbinden. | Vorher geöffnete Dateien müssen neu geöffnet werden. |
| `-o ServerAliveInterval=15` | Verbindung aktiv halten, Abbrüche erkennen. | Laut Manpage Abbruch nach etwa 45 s ohne Antwort. |
| `-o default_permissions` | Lokale Rechteprüfung einschalten. | Empfohlen mit `allow_other`. |
| `-o allow_other` | Andere lokale Konten zulassen. | Kann eine FUSE-Freigabe durch die Verwaltung erfordern. **Prüfpunkt:** nicht geprüft. |
| `-o IdentityFile=DATEI` | Bestimmten Schlüssel verwenden. | SSH-Optionen sind über `-o` möglich. |
| `-C` | Kompression. | – |
| `-f`, `-d` | Im Vordergrund bleiben bzw. Diagnose. | Fehlersuche. |
| `-o workaround=…` | Umgehungen für Serverbesonderheiten, etwa `rename`, `renamexdev`. | Siehe Manpage. |
| `-V` | Version. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Einen Serverordner einhängen, eine Datei bearbeiten und wieder aushängen. Das braucht einen SSH-Zugang; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Einhängepunkt anlegen

```bash
mkdir -p ~/mnt/server
```

Der Ordner muss dir gehören und sollte leer sein.

### Schritt 2: Einhängen

```bash
sshfs anna@server.example.org:/srv/daten ~/mnt/server -o idmap=user,reconnect,ServerAliveInterval=15
```

### Schritt 3: Arbeiten und prüfen

```bash
ls -l ~/mnt/server
findmnt ~/mnt/server
```

`findmnt` zeigt den Typ `fuse.sshfs`.

### Schritt 4: Aushängen

```bash
fusermount3 -u ~/mnt/server
```

Vorher Programme schließen, die Dateien darin offen haben.

## 6. Typische Anwendungsfälle

- **Dateien auf Servern** mit lokalen Programmen (Editor, Dateimanager) bearbeiten.
- **Gelegentlicher Zugriff** ohne Samba oder NFS.
- **Datensicherungen** von Servern mit lokalen Werkzeugen lesen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nicht zu: Alles im Einhängepunkt wirkt direkt auf dem Server. Der Kopf verwendet `caution`.

- **Löschen und Überschreiben** geschieht sofort auf dem Server; kein Papierkorb.
- **Rekursive Programme** (Indexdienste, Sicherungsprogramme, `find`, `du`) können über den Einhängepunkt viel Last und Datenverkehr erzeugen.
- **Hängende Programme:** Bei Verbindungsabbruch frieren Zugriffe laut Manpage ein. Hilfe: `ServerAliveInterval`, `reconnect`; im Notfall den `sshfs`-Prozess beenden, wobei ungeschriebene Daten verloren gehen können.
- **`allow_other` ohne `default_permissions`** gibt anderen lokalen Konten die vollen Rechte deines Serverkontos.
- **Sicherungen:** Einhängepunkte unter `~` können von Sicherungsprogrammen unbeabsichtigt mitgesichert werden.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `fuse: bad mount point …` | Einhängepunkt fehlt oder ist nicht leer. | Leeren eigenen Ordner verwenden. **Prüfpunkt:** Wortlaut nicht geprüft. |
| `read: Connection reset by peer` | SSH-Anmeldung gescheitert. | Erst `ssh` testen. |
| Programme frieren ein | Verbindung unterbrochen. | `ServerAliveInterval`, `reconnect`; Prozess beenden. |
| `Permission denied` beim Verschieben zwischen Server-Dateisystemen | Laut Manpage generischer SFTP-Fehler. | `-o workaround=renamexdev`. |
| Dateien gehören „fremden“ Nummern | Keine ID-Abbildung. | `-o idmap=user`. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Als normaler Benutzer** einhängen, nie mit `sudo`.
2. **`reconnect,ServerAliveInterval=15`** gegen Hänger.
3. **Kein `allow_other`** ohne Notwendigkeit.
4. **Nach der Arbeit aushängen.**
5. **Für große Übertragungen `rsync`** statt Kopieren im Einhängepunkt.

### Prüfstand

- **Geprüfte Version:** SSHFS 3.7.3 mit FUSE 3.14.0 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie.
- **Tatsächlich ausgeführt:** nur `sshfs --version`. Einhängen wurde bewusst nicht ausgeführt (kein Mount allein für Dokumentationszwecke).
- **Nicht geprüft:** jedes Einhängen, Optionen, Verbindungsabbrüche, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `fusermount3` | Hängt FUSE-Dateisysteme aus. |
| `sftp` | Interaktive Übertragung über dasselbe Protokoll. |
| `rsync`, `scp` | Kopieren statt Einhängen. |
| `findmnt` | Zeigt eingehängte Dateisysteme. |
| `ssh` | Grundlage der Verbindung. |

Ausgangseintrag: Datensatz 173 in `index.json` (`sshfs`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Funktionsweise, Rechte- und ID-Vorgaben, Optionen gegen Hänger und einen Ablauf zum Ein- und Aushängen ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
