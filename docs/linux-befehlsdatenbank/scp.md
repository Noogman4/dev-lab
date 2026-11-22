---
id: "scp"
name: "scp"
command: "scp"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "ssh", "dateiuebertragung"]
status: "Ausgearbeitet; Quellen geprüft; nur lokale Kopie praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 165
reviewed_at: "2026-11-13"
locally_checked_version: "OpenSSH 9.6p1 (Paket openssh-client 1:9.6p1-3ubuntu13.20)"
---

# scp – Dateien verschlüsselt zwischen Rechnern kopieren

## 1. Kurzbeschreibung

`scp` („secure copy“) kopiert Dateien zwischen Rechnern über eine **SSH-Verbindung**. Laut [Debian-Manpage zu scp](https://manpages.debian.org/trixie/openssh-client/scp.1.en.html) nutzt es dieselbe Anmeldung und bietet dieselbe Sicherheit wie eine SSH-Sitzung; neuere OpenSSH-Versionen übertragen die Daten dabei über das **SFTP-Protokoll**.

**Root-Rechte sind nicht nötig.** Du brauchst einen SSH-Zugang zum anderen Rechner und dort Lese- beziehungsweise Schreibrechte.

## 2. Was macht der Befehl?

`scp QUELLE ZIEL` kopiert wie `cp`, nur dass Quelle und Ziel auch auf anderen Rechnern liegen können:

- **Lokaler Pfad:** `datei.txt` oder `./ordner/datei.txt`.
- **Entfernter Pfad:** `[BENUTZER@]HOST:[PFAD]` – ohne Pfad ist das Heimatverzeichnis gemeint.
- **URI:** `scp://[BENUTZER@]HOST[:PORT][/PFAD]`.

Laut Manpage sollte man lokale Dateinamen mit `:` als Pfad kennzeichnen (`./name:mit:doppelpunkt`), sonst hält `scp` sie für eine Hostangabe.

Zwischen zwei entfernten Rechnern werden die Daten standardmäßig über den lokalen Rechner geleitet (`-3` ist Vorgabe).

**Protokollwechsel:** OpenSSH verwendet für `scp` inzwischen standardmäßig SFTP. Mit `-O` lässt sich das alte SCP-Protokoll erzwingen, etwa für Server ohne SFTP. Beim alten Protokoll wertet laut Manpage die Shell auf dem Server Platzhalter aus, was sorgfältiges Maskieren erfordert.

## 3. Syntax

```text
scp [OPTIONEN] QUELLE ... ZIEL
```

```bash
scp bericht.pdf anna@server.example.org:Dokumente/
scp -P 2222 anna@server.example.org:/var/log/app.log .
scp -r projekt/ anna@server.example.org:/srv/
```

Das bisherige NetMon-Beispiel `scp --help` ist keine gültige Option: Im Test meldete `scp` `unknown option -- -` und zeigte danach die Kurzübersicht. Der Platzhalter `scp [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-P PORT` | SSH-Port. | Großes `P`, weil `-p` andere Bedeutung hat. |
| `-p` | Änderungs-/Zugriffszeit und Rechte erhalten. | – |
| `-r` | Ordner rekursiv kopieren. | Folgt laut Manpage symbolischen Links. |
| `-i DATEI` | Bestimmten privaten Schlüssel verwenden. | – |
| `-J ZIEL` | Über einen Sprungrechner verbinden. | Wie `ProxyJump`. |
| `-l KBIT` | Bandbreite begrenzen (Kbit/s). | – |
| `-C` | Kompression. | – |
| `-O` | Altes SCP-Protokoll. | Nur bei Bedarf. |
| `-o OPTION` | SSH-Option im Format von `ssh_config`. | – |
| `-F DATEI` | Andere SSH-Konfigurationsdatei. | – |
| `-q` | Fortschritt und Warnungen ausblenden. | – |
| `-v` | Diagnose. | Für Anmeldeprobleme. |
| `-T` | Strenge Dateinamenprüfung abschalten. | Nur bewusst; siehe Abschnitt 7. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Eine Datei auf einen Server kopieren und eine Protokolldatei zurückholen. Das braucht einen SSH-Zugang; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: SSH-Zugang prüfen

```bash
ssh anna@server.example.org true
```

Funktioniert das ohne Fehler, funktioniert auch `scp` mit denselben Angaben.

### Schritt 2: Hochladen

```bash
scp bericht.pdf anna@server.example.org:Dokumente/
```

Ohne führenden `/` ist der Pfad relativ zum Heimatverzeichnis auf dem Server. Eine vorhandene Datei gleichen Namens wird überschrieben.

### Schritt 3: Herunterladen

```bash
scp anna@server.example.org:/var/log/app.log ./app-server.log
```

### Lokal geprüfte Grundfunktion

```bash
uebung="$(mktemp -d -t netmon-scp-XXXXXX)" || exit 1
echo x > "$uebung/a.txt"
scp "$uebung/a.txt" "$uebung/b.txt"
```

Ohne Hostangabe kopiert `scp` lokal wie `cp`; im Test entstand `b.txt`, Rückgabewert `0`.

## 6. Typische Anwendungsfälle

- **Einzelne Dateien** schnell auf einen Server bringen.
- **Protokolle oder Sicherungen** abholen.
- **Über Sprungrechner** in abgeschottete Netze kopieren (`-J`).

Für große Ordner oder wiederholte Abgleiche ist `rsync` besser geeignet, für interaktives Arbeiten `sftp`.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nicht zu: `scp` überschreibt Dateien auf beiden Seiten ohne Rückfrage. Der Kopf verwendet `caution`.

- **Überschreiben:** Gleichnamige Zieldateien werden ersetzt.
- **Verwechselte Reihenfolge:** `scp lokal server:pfad` lädt hoch, `scp server:pfad lokal` lädt herunter. Vertauscht überschreibt man die falsche Seite.
- **`-T`** schaltet laut Manpage eine Schutzprüfung ab, die verhindert, dass der Server unerwartete Dateinamen liefert.
- **Symbolische Links bei `-r`:** Werden verfolgt; dadurch können unerwartet Daten außerhalb des Ordners kopiert werden.
- **`-O` und Platzhalter:** Beim alten Protokoll wertet die entfernte Shell Muster aus; ungeschickt maskierte Namen können anders interpretiert werden.
- **Hostschlüssel:** Beim ersten Kontakt fragt SSH nach dem Fingerabdruck; nicht ungeprüft bestätigen.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `Permission denied (publickey,...)` | Anmeldung fehlgeschlagen. | Mit `ssh -v` prüfen. |
| `No such file or directory` | Pfad falsch, oft relativ statt absolut auf dem Server. | Mit `ssh HOST ls PFAD` prüfen. |
| Datei mit `:` im Namen wird als Host gedeutet | Doppelpunkt im Namen. | `./` voranstellen. |
| Verbindung auf falschem Port | `-p` statt `-P`. | `-P PORT`. |
| Platzhalter funktioniert nicht | SFTP-Modus wertet Muster anders aus. | Muster maskieren; notfalls `-O`. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Erst `ssh` testen,** dann `scp`.
2. **Absolute Pfade auf dem Server** verwenden, um Verwechslungen zu vermeiden.
3. **Für große oder wiederholte Übertragungen `rsync`.**
4. **Kein `-T`** ohne Grund.
5. **SSH-Schlüssel statt Passwörtern.**

### Prüfstand

- **Geprüfte Version:** OpenSSH 9.6p1 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie.
- **Tatsächlich ausgeführt:** Lokale Kopie einer eigenen Datei ohne Hostangabe (Rückgabe 0).
- **Nicht geprüft:** jede Übertragung über SSH, `-O`, `-J`, `-3`, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `sftp` | Interaktive Dateiübertragung über SSH. |
| `rsync` | Abgleich, Fortsetzen, Ausschlüsse. |
| `ssh` | Grundlage der Verbindung. |
| `sshfs` | Entfernte Ordner lokal einhängen. |

Ausgangseintrag: Datensatz 165 in `index.json` (`scp`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Pfadschreibweisen, Protokollwechsel zu SFTP, Optionen und Überschreibrisiken ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
