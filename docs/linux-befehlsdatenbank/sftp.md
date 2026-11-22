---
id: "sftp"
name: "sftp"
command: "sftp"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "ssh", "dateiuebertragung"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 166
reviewed_at: "2026-11-13"
locally_checked_version: "OpenSSH 9.6p1 (Paket openssh-client 1:9.6p1-3ubuntu13.20); nur Hilfe"
---

# sftp – Dateien interaktiv und verschlüsselt über SSH übertragen

## 1. Kurzbeschreibung

`sftp` ist laut [Debian-Manpage zu sftp](https://manpages.debian.org/trixie/openssh-client/sftp.1.en.html) ein Dateiübertragungsprogramm ähnlich `ftp`, das alle Vorgänge über eine **verschlüsselte SSH-Verbindung** ausführt. Es bietet eine interaktive Eingabeaufforderung (`sftp>`) mit Befehlen zum Auflisten, Herunterladen, Hochladen, Umbenennen und Löschen – und einen Stapelmodus für Skripte.

**Root-Rechte sind nicht nötig.** Du brauchst einen SSH-Zugang; auf dem Server muss das SFTP-Subsystem aktiv sein (bei OpenSSH üblich).

## 2. Was macht der Befehl?

`sftp [BENUTZER@]HOST` meldet sich per SSH an und startet die Eingabeaufforderung. Ist im Ziel ein Pfad zu einer Datei angegeben, lädt `sftp` diese direkt herunter. Ist der Pfad ein Ordner, wechselt `sftp` nach der Anmeldung dorthin.

Befehle im interaktiven Modus (Auswahl laut Manpage):

| Befehl | Wirkung |
| --- | --- |
| `ls`, `cd`, `pwd` | Entfernten Ordner ansehen bzw. wechseln. |
| `lls`, `lcd`, `lpwd` | Dasselbe lokal. |
| `get [-afpR] ENTFERNT [LOKAL]` | Herunterladen; `-a` setzt Teilübertragungen fort. |
| `put [-afpR] LOKAL [ENTFERNT]` | Hochladen. |
| `reget`, `reput` | Abgebrochene Übertragung fortsetzen. |
| `mkdir`, `rmdir`, `rm`, `rename` | Ordner anlegen/löschen, Dateien löschen/umbenennen. |
| `chmod`, `df` | Rechte ändern bzw. freien Platz anzeigen. |
| `help` | Befehle anzeigen. |
| `bye`, `quit` | Beenden. |

Für IPv6-Adressen verlangt die Manpage eckige Klammern, weil `:` Host und Pfad trennt.

## 3. Syntax

```text
sftp [OPTIONEN] [BENUTZER@]HOST[:PFAD]
sftp [OPTIONEN] sftp://[BENUTZER@]HOST[:PORT][/PFAD]
sftp -b STAPELDATEI [BENUTZER@]HOST
```

```bash
sftp anna@server.example.org
sftp -P 2222 anna@server.example.org:/srv/daten/
sftp -b befehle.txt anna@server.example.org
```

Das bisherige NetMon-Beispiel `sftp --help` ist keine gültige Option von OpenSSH; wie bei `scp` erscheint eine Kurzübersicht nach einer Fehlermeldung. Innerhalb einer Sitzung zeigt `help` die Befehle. Der Platzhalter `sftp [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-P PORT` | SSH-Port. | – |
| `-i DATEI` | Privater Schlüssel. | – |
| `-J ZIEL` | Über Sprungrechner verbinden. | – |
| `-b DATEI` | Stapelmodus; `-` für Standardeingabe. | Bricht bei Fehlern in `get`, `put`, `rm` usw. ab. |
| `-r` | Ordner rekursiv übertragen. | Folgt laut Manpage **keinen** symbolischen Links. |
| `-p` | Zeiten und Rechte erhalten. | – |
| `-q` | Fortschritt und Warnungen ausblenden. | – |
| `-o OPTION`, `-F DATEI` | SSH-Optionen bzw. -Konfiguration. | – |
| `-C` | Kompression. | – |

Im Stapelmodus lässt sich der Abbruch bei einem einzelnen Befehl durch ein vorangestelltes `-` unterdrücken (etwa `-rm datei`), ein vorangestelltes `@` unterdrückt die Ausgabe des Befehls.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Auf einem Server einen Ordner ansehen, eine Datei herunterladen und eine hochladen. Das braucht einen SSH-Zugang; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Verbinden

```bash
sftp anna@server.example.org
```

### Schritt 2: Umsehen

```text
sftp> pwd
sftp> ls -l
sftp> lpwd
```

`pwd`/`ls` gelten für den Server, `lpwd` für den eigenen Rechner.

### Schritt 3: Herunter- und hochladen

```text
sftp> get bericht.pdf
sftp> put notizen.txt Dokumente/notizen.txt
sftp> bye
```

### Stapelmodus für Skripte

```bash
printf 'cd /srv/upload\nput daten.csv\n' > befehle.txt
sftp -b befehle.txt anna@server.example.org
```

Der Stapelmodus braucht eine Anmeldung ohne Passwortabfrage, etwa per SSH-Schlüssel.

## 6. Typische Anwendungsfälle

- **Interaktives Arbeiten** auf Servern ohne Shell-Zugang (nur SFTP erlaubt).
- **Sichere Alternative zu FTP.**
- **Automatisierte Übertragungen** im Stapelmodus.
- **Fortsetzen** abgebrochener Übertragungen mit `reget`/`reput`.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nicht zu: `sftp` kann auf dem Server löschen, umbenennen und überschreiben. Der Kopf verwendet `caution`.

- **`rm`, `rmdir`, `rename`** wirken sofort auf dem Server; es gibt keinen Papierkorb.
- **Überschreiben:** `get` und `put` ersetzen gleichnamige Dateien.
- **Fortsetzen mit `-a`:** Laut Manpage setzt das voraus, dass die lokale Teilkopie zur entfernten Datei passt; sonst entsteht eine beschädigte Datei.
- **Platzhalter bei `get`/`rm`:** Muster können mehr Dateien treffen als gedacht.
- **Stapelmodus mit `-`-Präfix** unterdrückt Fehler und kann Folgeschritte mit falschen Annahmen ausführen.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `Permission denied (publickey,...)` | Anmeldung fehlgeschlagen. | `ssh -v` zur Diagnose. |
| `subsystem request failed` | SFTP auf dem Server nicht aktiv. | Serverkonfiguration prüfen lassen. |
| `Couldn't stat remote file` | Pfad falsch. | `ls` und `pwd` prüfen. |
| Stapelmodus bricht ab | Ein Befehl schlug fehl. | Befehl prüfen oder bewusst mit `-` versehen. |
| IPv6-Adresse wird falsch gelesen | Doppelpunkte. | Eckige Klammern verwenden. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **`pwd` und `lpwd` prüfen,** bevor du überträgst.
2. **Vor `rm` mit Mustern erst `ls` mit demselben Muster.**
3. **SSH-Schlüssel** für den Stapelmodus.
4. **Für große Abgleiche `rsync`.**

### Prüfstand

- **Geprüfte Version:** OpenSSH 9.6p1 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie.
- **Tatsächlich ausgeführt:** keine Verbindung; nur `sftp --help` (Meldung `unknown option -- -` mit Kurzübersicht).
- **Nicht geprüft:** jede Sitzung, Stapelmodus, Fortsetzen, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `scp` | Einzelne Kopien über SSH. |
| `rsync` | Abgleich großer Datenmengen. |
| `ftp` | Unverschlüsselter Vorgänger mit ähnlicher Bedienung. |
| `sshfs` | Entfernte Ordner per SFTP einhängen. |
| `ssh` | Grundlage der Verbindung. |

Ausgangseintrag: Datensatz 166 in `index.json` (`sftp`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Befehle der Sitzung, Stapelmodus, Optionen und Risiken beim Löschen und Fortsetzen ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
