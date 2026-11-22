---
id: "ssh_copy_id"
name: "ssh-copy-id"
command: "ssh-copy-id"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "ssh", "schluessel", "anmeldung"]
status: "Ausgearbeitet; Quellen geprüft; Probelauf ohne Verbindung geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 171
reviewed_at: "2026-11-13"
locally_checked_version: "ssh-copy-id aus OpenSSH 9.6p1 (Paket openssh-client 1:9.6p1-3ubuntu13.20)"
---

# ssh-copy-id – Öffentlichen SSH-Schlüssel auf einem Server hinterlegen

## 1. Kurzbeschreibung

`ssh-copy-id` richtet die **Anmeldung per SSH-Schlüssel** auf einem entfernten Rechner ein. Es meldet sich – meist noch mit Passwort – per `ssh` an und hängt deinen öffentlichen Schlüssel an die Datei `~/.ssh/authorized_keys` des Zielkontos an. Danach kannst du dich mit dem passenden privaten Schlüssel anmelden.

**Root-Rechte sind auf dem eigenen Rechner nicht nötig.** Auf dem Server wird nur das Zielkonto verändert; dafür brauchst du dessen Zugangsdaten.

Grundlage ist die [Debian-Manpage zu ssh-copy-id](https://manpages.debian.org/trixie/openssh-client/ssh-copy-id.1.en.html). `ssh-copy-id` ist ein Shell-Skript, das `ssh` beziehungsweise `sftp` aufruft.

## 2. Was macht der Befehl?

Laut Manpage:

1. Es stellt eine Liste von Schlüsseln zusammen: mit `-i` aus der angegebenen Datei, sonst aus `ssh-add -L` (geladene Agent-Schlüssel) oder aus der neuesten Datei `~/.ssh/id*.pub`.
2. Es versucht sich mit jedem Schlüssel anzumelden, um bereits installierte herauszufiltern.
3. Für die übrigen meldet es sich an und **hängt sie an** `~/.ssh/authorized_keys` an; Datei und Ordner werden bei Bedarf angelegt.

Nur **öffentliche** Schlüssel (`.pub`) werden übertragen. Der private Schlüssel verlässt den Rechner nicht.

## 3. Syntax

```text
ssh-copy-id [-f] [-n] [-s] [-i [DATEI]] [-p PORT] [-o OPTION] [BENUTZER@]HOST
```

```bash
ssh-copy-id anna@server.example.org
ssh-copy-id -i ~/.ssh/id_ed25519.pub -p 2222 anna@server.example.org
ssh-copy-id -f -n -i ~/.ssh/id_ed25519.pub anna@server.example.org
```

Das bisherige NetMon-Beispiel `ssh-copy-id --help` ist keine dokumentierte Form; die Kurzhilfe zeigen laut Manpage `-h` oder `-?`. Der Platzhalter `ssh-copy-id [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-i [DATEI]` | Nur diesen Schlüssel verwenden. | `.pub` wird ergänzt, falls es fehlt. |
| `-n` | Probelauf: zeigt, welche Schlüssel hinzugefügt würden. | Meldet sich zum Filtern trotzdem an, außer mit `-f`. |
| `-f` | Nicht prüfen, ob der Schlüssel schon vorhanden ist. | Kann doppelte Einträge erzeugen. |
| `-s` | SFTP-Modus: Datei herunterladen, lokal ändern, hochladen. | Für Server mit eingeschränkten Befehlen. |
| `-t PFAD` | Anderer Zielpfad als `.ssh/authorized_keys`. | – |
| `-p PORT` | SSH-Port. | – |
| `-o OPTION`, `-F DATEI` | Werden an `ssh`/`sftp` weitergereicht. | – |
| `-x` | Skript mit Ablaufprotokoll ausführen. | Fehlersuche. |
| `-h`, `-?` | Kurzhilfe. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Einen neuen Schlüssel erzeugen, im Probelauf sehen, was übertragen würde, und ihn dann auf einem Server einrichten. Der letzte Schritt braucht einen Server und ist ein **Beispielszenario**; die ersten Schritte wurden mit einem Testschlüssel geprüft.

### Schritt 1: Schlüssel erzeugen (Beispiel)

```bash
ssh-keygen -t ed25519 -C "anna@laptop"
```

Mit Passphrase; siehe `ssh-keygen`.

### Schritt 2: Probelauf ohne Verbindung (geprüft)

```bash
ssh-copy-id -f -n -i ~/.ssh/id_ed25519.pub anna@server.example.org
```

Ausgabe im Test: `Would have added the following key(s):` und der öffentliche Schlüssel. Durch `-f` versucht `ssh-copy-id` keine Anmeldung; ohne `-f` versuchte es auch bei `-n` eine Verbindung, um vorhandene Schlüssel herauszufiltern.

### Schritt 3: Einrichten

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub anna@server.example.org
```

`ssh-copy-id` fragt nach dem Passwort von `anna` und meldet die Zahl der hinzugefügten Schlüssel.

### Schritt 4: Prüfen

```bash
ssh -i ~/.ssh/id_ed25519 anna@server.example.org
```

Die Anmeldung sollte jetzt ohne Kontopasswort funktionieren (gegebenenfalls mit Schlüssel-Passphrase).

## 6. Typische Anwendungsfälle

- **Ersteinrichtung** der Schlüsselanmeldung auf einem neuen Server.
- **Weiteren Rechner** (Laptop, Arbeitsplatz) für ein Konto freischalten.
- **Server mit eingeschränkter Shell** über `-s`.
- **Vorbereitung** für das Abschalten der Passwortanmeldung auf dem Server.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nicht zu: `ssh-copy-id` verändert die Zugangsregeln auf einem anderen Rechner. Der Kopf verwendet `caution`.

- **Dauerhafter Zugang:** Jeder hinterlegte Schlüssel öffnet das Konto, bis er aus `authorized_keys` entfernt wird.
- **Falscher Schlüssel:** Ohne `-i` wählt `ssh-copy-id` Schlüssel aus dem Agenten oder die neueste `~/.ssh/id*.pub`-Datei; das kann ein anderer sein als gedacht. Laut Manpage übernimmt der Kommentar bei Agent-Schlüsseln den Dateinamen.
- **Doppelte Einträge mit `-f`.**
- **Ungeschützte private Schlüssel:** Ein Schlüssel ohne Passphrase gibt jedem, der die Datei erhält, Zugang zum Server.
- **Hostschlüssel prüfen:** Die erste Verbindung fragt nach dem Fingerabdruck des Servers.

## 8. Häufige Fehler

| Meldung | Ursache | Vorgehen |
| --- | --- | --- |
| `ERROR: ssh: Could not resolve hostname …` | Name nicht auflösbar (im Test mit `beispiel.invalid` ohne `-f`). | Namen prüfen. |
| `ERROR: No identities found` | Kein Schlüssel im Agenten und keine `~/.ssh/id*.pub`. | Erst `ssh-keygen` ausführen. **Prüfpunkt:** Wortlaut nicht ausgelöst. |
| `Permission denied` | Passwortanmeldung auf dem Server abgeschaltet oder falsches Passwort. | Anderen Zugang nutzen oder Schlüssel von der Verwaltung eintragen lassen. |
| Anmeldung fragt weiter nach Passwort | Falsche Rechte auf `~/.ssh` oder `authorized_keys` des Servers. | Dort `700` bzw. `600` setzen. **Prüfpunkt:** Serververhalten nicht geprüft. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Immer `-i` angeben,** damit der richtige Schlüssel übertragen wird.
2. **Erst `-f -n`** für einen Probelauf ohne Verbindung.
3. **Schlüssel mit Passphrase** erzeugen.
4. **Nach dem Einrichten testen,** bevor die Passwortanmeldung abgeschaltet wird.
5. **Alte Schlüssel** auf Servern regelmäßig aus `authorized_keys` entfernen.

### Prüfstand

- **Geprüfte Version:** `ssh-copy-id` aus OpenSSH 9.6p1 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie.
- **Tatsächlich ausgeführt** mit einem Testschlüssel: `-n -i` gegen einen nicht auflösbaren Namen (Verbindungsversuch und Fehlermeldung) und `-f -n -i` (Ausgabe des Schlüssels ohne Verbindung).
- **Nicht geprüft:** tatsächliches Einrichten auf einem Server, `-s`, `-t`, Fehlermeldungen des Servers.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ssh-keygen` | Erzeugt das Schlüsselpaar. |
| `ssh` | Anmeldung mit dem Schlüssel. |
| `ssh-add` | Lädt Schlüssel in den Agenten; `ssh-copy-id` nutzt dessen Liste. |
| `sftp` | Wird im Modus `-s` verwendet. |

Ausgangseintrag: Datensatz 171 in `index.json` (`ssh-copy-id`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Ablauf, Schlüsselauswahl, Optionen, Probelauf und Risiken dauerhafter Zugänge ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
