---
id: "ssh"
name: "ssh"
command: "ssh"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "ssh", "fernzugriff", "weiterleitung"]
status: "Ausgearbeitet; Quellen geprüft; nur Konfigurationsauswertung praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 168
reviewed_at: "2026-11-13"
locally_checked_version: "OpenSSH 9.6p1 (Paket openssh-client 1:9.6p1-3ubuntu13.20)"
---

# ssh – Verschlüsselt auf anderen Rechnern anmelden und Befehle ausführen

## 1. Kurzbeschreibung

`ssh` (Secure Shell) baut eine **verschlüsselte Verbindung** zu einem anderen Rechner auf. Damit meldest du dich an einer entfernten Shell an, führst einzelne Befehle aus oder leitest Ports sicher weiter. Es ist das Standardwerkzeug für die Fernverwaltung von Linux-Servern.

**Root-Rechte sind nicht nötig.** Du brauchst ein Konto auf dem Zielrechner. Nur das Weiterleiten privilegierter lokaler Ports (unter 1024) erfordert laut [Debian-Manpage zu ssh](https://manpages.debian.org/trixie/openssh-client/ssh.1.en.html) Root-Rechte.

## 2. Was macht der Befehl?

`ssh [BENUTZER@]HOST` verbindet sich mit dem SSH-Dienst (Port 22), prüft den **Hostschlüssel** des Servers, meldet dich an (Schlüssel, Passwort oder andere Verfahren) und startet deine Shell auf dem Server. Mit einem angehängten Befehl wird nur dieser ausgeführt.

### Hostschlüssel

Beim ersten Kontakt zeigt `ssh` den **Fingerabdruck** des Serverschlüssels und fragt, ob er vertrauenswürdig ist (Vorgabe `StrictHostKeyChecking ask`). Nach der Bestätigung wird er in `~/.ssh/known_hosts` gespeichert. Ändert sich der Schlüssel später, warnt `ssh` deutlich – das kann ein Angriff oder eine Neuinstallation sein. Laut Manpage lässt sich der Fingerabdruck auf dem Server mit `ssh-keygen -l -f /etc/ssh/ssh_host_…_key` prüfen.

### Konfiguration

Einstellungen kommen aus der Befehlszeile, `~/.ssh/config` und `/etc/ssh/ssh_config`. `ssh -G HOST` zeigt die wirksame Konfiguration, ohne eine Verbindung aufzubauen.

### Rückgabewert

Laut Manpage gibt `ssh` den Rückgabewert des entfernten Befehls zurück oder `255` bei einem Fehler von `ssh` selbst.

## 3. Syntax

```text
ssh [OPTIONEN] [BENUTZER@]HOST [BEFEHL]
ssh [OPTIONEN] ssh://[BENUTZER@]HOST[:PORT] [BEFEHL]
```

```bash
ssh anna@server.example.org
ssh -p 2222 anna@server.example.org 'df -h'
ssh -J sprung.example.org intern.example.org
ssh -N -L 8080:localhost:80 anna@server.example.org
```

Das bisherige NetMon-Beispiel `ssh --help` ist keine gültige Option; OpenSSH zeigt dann nur eine Kurzübersicht. Der Platzhalter `ssh [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-p PORT` | Anderer Port. | Kleines `p` (bei `scp` großes `P`). |
| `-l BENUTZER` | Benutzername. | Alternativ `BENUTZER@HOST`. |
| `-i DATEI` | Bestimmter privater Schlüssel. | – |
| `-J ZIEL` | Über Sprungrechner verbinden. | Wie `ProxyJump`. |
| `-L [ADR:]PORT:HOST:PORT` | Lokalen Port über den Server weiterleiten. | `localhost` als Adresse: nur lokal erreichbar. |
| `-R [ADR:]PORT:HOST:PORT` | Port auf dem Server zum lokalen Rechner weiterleiten. | Öffnet einen Zugang auf dem Server. |
| `-D [ADR:]PORT` | Dynamische Weiterleitung (SOCKS-Proxy). | – |
| `-N` | Keinen Befehl ausführen, nur Weiterleitungen. | – |
| `-t` | Pseudo-Terminal erzwingen. | Für interaktive Programme in einem Befehl. |
| `-A` | Agent-Weiterleitung. | Laut Manpage mit Vorsicht verwenden. |
| `-X` | X11-Weiterleitung. | Laut Manpage mit Vorsicht verwenden. |
| `-o OPTION=WERT` | Konfigurationsoption setzen. | – |
| `-v`, `-vv`, `-vvv` | Diagnose. | Bei Anmeldeproblemen. |
| `-G` | Wirksame Konfiguration ausgeben und beenden. | Keine Verbindung. |
| `-V` | Version. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Prüfen, welche Einstellungen für einen Server gelten, und sich dann anmelden. Die Anmeldung braucht ein Konto auf dem Server; dieser Teil ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Wirksame Konfiguration ansehen (geprüft)

```bash
ssh -G -p 2222 -l anna beispiel.invalid
```

Ohne Verbindung zeigt `ssh` unter anderem `user anna`, `port 2222`, `stricthostkeychecking ask`, die Liste der Standardschlüssel unter `~/.ssh/` und `forwardagent no`.

### Schritt 2: Anmelden

```bash
ssh -p 2222 anna@server.example.org
```

Beim ersten Mal erscheint der Fingerabdruck des Servers. Vergleiche ihn mit einem auf anderem Weg erhaltenen Wert, bevor du `yes` eingibst.

### Schritt 3: Einzelnen Befehl ausführen

```bash
ssh anna@server.example.org 'uptime'
echo $?
```

Der Rückgabewert stammt von `uptime` auf dem Server; `255` hieße, dass `ssh` selbst gescheitert ist.

## 6. Typische Anwendungsfälle

- **Serververwaltung** über eine Shell.
- **Einzelbefehle in Skripten** (`ssh host 'befehl'`).
- **Sichere Tunnel** zu Datenbanken oder Weboberflächen (`-L`).
- **Zugang über Sprungrechner** (`-J`).
- **Grundlage für `scp`, `sftp`, `rsync`, `sshfs`.**

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nicht zu: `ssh` gibt vollen Zugriff auf einen anderen Rechner. Der Kopf verwendet `caution`.

- **Fingerabdrücke nicht ungeprüft bestätigen;** sonst ist ein Mittelsmann-Angriff möglich. Eine Warnung über einen geänderten Schlüssel nicht einfach durch Löschen des Eintrags „beheben“, ohne den Grund zu kennen.
- **Agent-Weiterleitung (`-A`):** Laut Manpage können Personen mit Root-Rechten auf dem Server den weitergeleiteten Agenten nutzen und sich damit als du an anderen Rechnern anmelden.
- **X11-Weiterleitung (`-X`):** Laut Manpage können solche Personen auf deine lokale Anzeige zugreifen, etwa Tastatureingaben mitlesen.
- **Weiterleitungen öffnen Zugänge:** `-R` oder `-L` mit leerer Adresse beziehungsweise `*` machen Ports für andere erreichbar.
- **`StrictHostKeyChecking=no`** in Skripten schaltet die Hostschlüsselprüfung ab.
- **Befehle mit Root-Rechten auf dem Server** wirken dort wie lokal: Fehler betreffen das entfernte System.

## 8. Häufige Fehler

| Meldung | Ursache | Vorgehen |
| --- | --- | --- |
| `Permission denied (publickey,password)` | Anmeldung abgelehnt. | Benutzer, Schlüssel und `-v` prüfen. |
| `Connection refused` | Kein SSH-Dienst auf dem Port. | Port und Dienst prüfen. |
| `Connection timed out` | Firewall oder falsche Adresse. | Netz und Adresse prüfen. |
| `Host key verification failed.` | Hostschlüssel unbekannt (ohne Bestätigung) oder geändert. | Fingerabdruck prüfen; Eintrag nur nach Klärung mit `ssh-keygen -R HOST` entfernen. |
| `WARNING: UNPROTECTED PRIVATE KEY FILE!` | Schlüsseldatei für andere lesbar. | `chmod 600 SCHLÜSSEL`. |
| `unknown option -- -` | Lange Option wie `--help`. | Manpage lesen. |

Die Meldungen zu Hostschlüssel und Schlüsselrechten sind im lokalen Programm enthalten; ausgelöst wurde nur `unknown option -- -`. **Prüfpunkt:** Die übrigen Wortlaute stammen aus Systembibliotheken oder vom Server und sind sinngemäß.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **SSH-Schlüssel statt Passwörtern** (`ssh-keygen`, `ssh-copy-id`).
2. **Fingerabdrücke prüfen.**
3. **Häufige Ziele in `~/.ssh/config`** mit Namen, Port und Schlüssel hinterlegen.
4. **`-A` und `-X` nur bei vertrauenswürdigen Servern.**
5. **Weiterleitungen mit `localhost` binden.**
6. **Mit `ssh -G` prüfen,** welche Einstellungen wirklich gelten.

### Prüfstand

- **Geprüfte Version:** OpenSSH 9.6p1 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie.
- **Tatsächlich ausgeführt:** `ssh -V`, `ssh -G` für einen nicht existierenden Namen (Auswertung ohne Verbindung), `ssh --help` (Meldung `unknown option -- -` mit Kurzübersicht); Abgleich der Meldungstexte zu Hostschlüssel und Schlüsselrechten im Programm.
- **Nicht geprüft:** jede Verbindung, Weiterleitungen, Agent- und X11-Weiterleitung, Fehlermeldungen beim Anmelden.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ssh-keygen` | Schlüssel erzeugen und Fingerabdrücke anzeigen. |
| `ssh-copy-id` | Öffentlichen Schlüssel auf dem Server hinterlegen. |
| `ssh-agent`, `ssh-add` | Entschlüsselte Schlüssel für eine Sitzung bereithalten. |
| `scp`, `sftp`, `rsync` | Dateien über SSH übertragen. |
| `mosh` | Robuster Fernzugang auf Basis von SSH. |
| `sshfs` | Entfernte Ordner einhängen. |

Ausgangseintrag: Datensatz 168 in `index.json` (`ssh`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Verbindungsablauf, Hostschlüsselprüfung, Optionen, Weiterleitungsrisiken und Rückgabewerte ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
