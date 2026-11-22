---
id: "ftp"
name: "ftp"
command: "ftp"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "dateiuebertragung", "ftp"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 154
reviewed_at: "2026-11-13"
locally_checked_version: "tnftp 20230507 (Paket tnftp 20230507-2build3, als ftp verlinkt); Hilfe; file://-Abruf scheiterte"
---

# ftp – Dateien mit dem File Transfer Protocol übertragen

## 1. Kurzbeschreibung

`ftp` ist ein Client für das **File Transfer Protocol**. Er meldet sich an einem FTP-Server an, zeigt Verzeichnisse an und lädt Dateien herunter oder hoch. Er kann interaktiv mit einer eigenen Eingabeaufforderung (`ftp>`) oder für einzelne Downloads direkt aus der Befehlszeile verwendet werden.

**Root-Rechte sind nicht nötig.** Du brauchst Zugangsdaten für den Server (oder anonymen Zugang) und Schreibrechte im lokalen Zielordner.

**Wichtig:** Klassisches FTP überträgt **Benutzername, Passwort und Daten unverschlüsselt**. Für vertrauliche Daten sind `sftp`, `scp` oder `rsync` über SSH die bessere Wahl.

### Welches Programm ist `ftp`?

Unter Debian und Ubuntu verweist `ftp` über das Alternativen-System auf eine von mehreren Implementierungen. Auf dem geprüften System ist es **tnftp** (`/usr/bin/ftp → /etc/alternatives/ftp → /usr/bin/tnftp`). Andere Systeme verwenden die Fassung aus `inetutils-ftp` mit teils anderen Optionen. Dieses Dokument folgt der [Debian-Manpage zu tnftp](https://manpages.debian.org/trixie/tnftp/tnftp.1.en.html).

## 2. Was macht der Befehl?

**Interaktiver Modus:** `ftp HOST` verbindet sich, fragt nach Anmeldedaten (oder liest sie aus `~/.netrc`) und öffnet die Eingabeaufforderung `ftp>`. Dort gelten eigene Befehle:

| Befehl | Wirkung |
| --- | --- |
| `ls`, `cd`, `pwd` | Entferntes Verzeichnis ansehen bzw. wechseln. |
| `lcd ORDNER` | Lokales Verzeichnis wechseln. |
| `get DATEI`, `mget MUSTER` | Herunterladen. |
| `put DATEI`, `mput MUSTER` | Hochladen. |
| `delete DATEI`, `mdelete MUSTER` | Auf dem Server löschen. |
| `binary`, `ascii` | Übertragungsart; laut Manpage ist interaktiv `ascii` Vorgabe. |
| `passive` | Passiven Modus umschalten. |
| `prompt` | Rückfragen bei Mehrfachübertragungen umschalten. |
| `bye`, `quit` | Beenden. |

**Auto-Fetch:** Werden URLs oder `HOST:PFAD` auf der Befehlszeile übergeben, lädt tnftp die Dateien direkt in den aktuellen Ordner – laut Manpage geeignet für Skripte. Dabei ist die Übertragungsart `binary` Vorgabe.

## 3. Syntax

```text
ftp [OPTIONEN] [[BENUTZER@]HOST [PORT]]
ftp [OPTIONEN] ftp://[BENUTZER[:PASSWORT]@]HOST[:PORT]/PFAD
ftp [OPTIONEN] -o ZIEL URL
```

```bash
ftp ftp.example.org
ftp -a ftp.example.org
ftp -o liesmich.txt ftp://ftp.example.org/pub/liesmich.txt
```

Das bisherige NetMon-Beispiel `ftp --help` ist bei tnftp keine dokumentierte Option; die Kurzübersicht erscheint mit einer ungültigen Option wie `ftp -?`. Der Platzhalter `ftp [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-a` | Anonym anmelden. | Für öffentliche Server. |
| `-n` | Keine automatische Anmeldung über `~/.netrc`. | – |
| `-N DATEI` | Andere netrc-Datei. | – |
| `-o ZIEL` | Ziel für Auto-Fetch; `-` für Standardausgabe. | – |
| `-i` | Keine Rückfragen bei Mehrfachübertragungen. | Vorsicht bei `mdelete`. |
| `-A` | Aktiven Modus erzwingen. | Nur für sehr alte Server. |
| `-p` | Passiven Modus aktivieren. | Laut Manpage veraltet, weil passiv ohnehin Vorgabe. |
| `-v` | Ausführliche Ausgabe. | Vorgabe im Terminal. |
| `-4`, `-6` | Nur IPv4 bzw. IPv6. | – |
| `-P PORT` | Anderer Port. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Von einem öffentlichen FTP-Server eine Datei anonym herunterladen. Das braucht Netzwerkzugang; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Verbinden

```bash
ftp -a ftp.example.org
```

Nach der Anmeldung erscheint `ftp>`.

### Schritt 2: Umsehen

```text
ftp> ls
ftp> cd pub
ftp> binary
```

`binary` stellt sicher, dass Archive und Programme nicht verändert werden.

### Schritt 3: Herunterladen

```text
ftp> lcd /tmp
ftp> get liesmich.txt
ftp> bye
```

Die Datei liegt danach im lokalen Ordner `/tmp`.

### Kurzform für Skripte

```bash
ftp -o liesmich.txt ftp://ftp.example.org/pub/liesmich.txt
```

## 6. Typische Anwendungsfälle

- **Öffentliche Archive** (Softwarespiegel) anonym nutzen.
- **Ältere Geräte und Dienste,** die nur FTP anbieten (Drucker, Kameras, Webhosting).
- **Einfache Downloads in Skripten** über Auto-Fetch.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nicht zu: FTP kann Dateien hochladen und löschen und überträgt Zugangsdaten im Klartext. Der Kopf verwendet `caution`.

- **Klartext:** Passwörter und Inhalte können im Netz mitgelesen werden.
- **Passwörter in URLs** (`ftp://name:passwort@...`) erscheinen in Shell-Verlauf und Prozessliste.
- **`~/.netrc`** speichert Passwörter; die Datei darf nur für dich lesbar sein.
- **Hochladen und Löschen:** `put`, `mput`, `delete`, `mdelete` verändern den Server; mit `-i` oder ausgeschaltetem `prompt` ohne Rückfrage.
- **Übertragungsart:** Im interaktiven Modus ist `ascii` laut Manpage Vorgabe; Binärdateien können dabei beschädigt werden. Vor Übertragungen `binary` setzen.
- **Überschreiben lokal:** `get` ersetzt vorhandene lokale Dateien gleichen Namens. **Prüfpunkt:** nicht geprüft.
- **Firewalls:** FTP nutzt getrennte Daten- und Steuerverbindungen; im aktiven Modus baut der Server eine Verbindung zum Client auf.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `530 Login incorrect` | Falsche Zugangsdaten. | Prüfen; anonyme Server mit `-a`. |
| Verbindung hängt beim `ls` | Daten- oder Firewallproblem. | Passiven Modus nutzen (Vorgabe), Firewall prüfen. |
| Beschädigte Archive | `ascii`-Übertragung. | `binary` vor `get` oder `put`. |
| `Not connected.` | Befehl ohne Verbindung. | `open HOST`. |
| `ftp: ftp_strdup: called with NULL argument` | Auf dem Prüfsystem beim Auto-Fetch einer `file://`-URL beobachtet. | **Prüfpunkt:** Ursache nicht geklärt. |

Die dreistelligen Codes (`530` usw.) sind Antworten des Servers; Wortlaute hängen vom Server ab.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Wenn möglich `sftp` statt `ftp`.**
2. **Nur anonyme oder nicht vertrauliche Übertragungen** über unverschlüsseltes FTP.
3. **Vor Übertragungen `binary`.**
4. **Keine Passwörter in URLs oder der Befehlszeile.**
5. **`prompt` eingeschaltet lassen,** besonders vor `mdelete`.

### Prüfstand

- **Geprüfte Version:** tnftp 20230507 (Ubuntu-Paket), über Alternativen als `ftp` eingerichtet.
- **Tatsächlich ausgeführt:** Ermittlung der Implementierung über die Verweise, Kurzhilfe mit `ftp -?`, Auto-Fetch einer eigenen `file://`-Datei mit und ohne `-o`. Der Abruf scheiterte jeweils mit `ftp: ftp_strdup: called with NULL argument`; es entstand keine Datei.
- **Nicht geprüft:** jede Verbindung zu einem FTP-Server, interaktive Befehle, `.netrc`, Fehlermeldungen von Servern.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `sftp` | Interaktive Dateiübertragung über SSH, verschlüsselt. |
| `scp`, `rsync` | Kopieren über SSH. |
| `curl`, `wget` | Können FTP-URLs ebenfalls abrufen. |

Ausgangseintrag: Datensatz 154 in `index.json` (`ftp`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch die Einordnung der Implementierung, interaktive Befehle, Auto-Fetch, Klartext-Risiken und Übertragungsarten ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
