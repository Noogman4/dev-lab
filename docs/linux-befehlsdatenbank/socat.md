---
id: "socat"
name: "socat"
command: "socat"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "sockets", "weiterleitung", "fehlersuche"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel mit Unix-Socket geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 167
reviewed_at: "2026-11-13"
locally_checked_version: "socat 1.8.0.0 (Paket socat 1.8.0.0-4ubuntu0.1)"
---

# socat – Zwei beliebige Datenkanäle miteinander verbinden

## 1. Kurzbeschreibung

`socat` („SOcket CAT“) verbindet laut [Debian-Manpage zu socat](https://manpages.debian.org/trixie/socat/socat.1.en.html) **zwei bidirektionale Datenströme** und überträgt Daten zwischen ihnen. Jede Seite kann ein anderer Typ sein: Datei, Standardein- und -ausgabe, TCP- oder UDP-Verbindung, Unix-Socket, Pipe, serielle Schnittstelle, TLS-Verbindung oder ein gestartetes Programm. Damit ist `socat` eine Art Universaladapter für Weiterleitungen, Tests und Fehlersuche.

**Root-Rechte sind meist nicht nötig.** Ausnahmen: Ports unter 1024, Geräte ohne Zugriffsrecht und einige Sonderadressen.

## 2. Was macht der Befehl?

Ein Aufruf hat immer genau **zwei Adressen**:

```text
socat [OPTIONEN] ADRESSE1 ADRESSE2
```

Laut Manpage öffnet `socat` erst die erste, dann die zweite Adresse und leitet danach Daten in beide Richtungen weiter, bis eine Seite endet. Mit `-u` nur von Adresse 1 nach Adresse 2.

Häufige Adresstypen:

| Adresse | Bedeutung |
| --- | --- |
| `-` oder `STDIO` | Standardein- und -ausgabe. |
| `FILE:PFAD`, `OPEN:PFAD`, `CREATE:PFAD` | Datei lesen/schreiben bzw. anlegen. |
| `TCP:HOST:PORT`, `TCP-LISTEN:PORT` | TCP-Verbindung aufbauen bzw. annehmen. |
| `UDP:HOST:PORT`, `UDP-LISTEN:PORT` | UDP. |
| `UNIX-CONNECT:PFAD`, `UNIX-LISTEN:PFAD` | Unix-Domain-Socket. |
| `OPENSSL:HOST:PORT` | TLS-Verbindung. |
| `EXEC:BEFEHL`, `SYSTEM:BEFEHL` | Programm starten und dessen Ein-/Ausgabe verbinden. |

Adressoptionen werden mit Komma angehängt, etwa `TCP-LISTEN:8080,fork,reuseaddr` oder `OPEN:datei,creat,wronly`.

## 3. Syntax

```text
socat [-d] [-u] [-v] ADRESSE1[,OPTION...] ADRESSE2[,OPTION...]
```

```bash
socat - TCP:example.org:80
socat TCP-LISTEN:8080,bind=127.0.0.1,fork TCP:intern.example:80
socat -u FILE:quelle.txt CREATE:kopie.txt
```

Das bisherige NetMon-Beispiel `socat --help` funktioniert nicht: Im Test meldete `socat` `unknown option "--help"; use option "-h" for help`. Die Hilfe erscheint mit `socat -h`, die Version mit `socat -V`. Der Platzhalter `socat [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-u` | Nur von Adresse 1 nach Adresse 2. | Verhindert Lesefehler auf reinen Schreibzielen. |
| `-U` | Nur von Adresse 2 nach Adresse 1. | – |
| `-d`, `-d0` | Mehr bzw. weniger Meldungen. | – |
| `-v`, `-x` | Übertragene Daten als Text bzw. Hex mitprotokollieren. | Zeigt auch vertrauliche Inhalte. |
| `fork` | Für jede Verbindung einen Kindprozess; weiter lauschen. | Für dauerhafte Weiterleitungen. |
| `bind=ADRESSE` | Lokale Adresse festlegen. | `127.0.0.1` für nur lokale Dienste. |
| `range=NETZ` | Nur Verbindungen aus diesem Bereich annehmen. | Zugriffskontrolle. |
| `reuseaddr` | Port trotz kürzlicher Nutzung wieder belegen. | Laut Manpage ab 1.8.0 bei TCP-LISTEN automatisch. |
| `creat`, `wronly`, `append` | Datei anlegen, nur schreiben, anhängen. | – |
| `unlink-early`, `unlink-close` | Dateisystemeintrag vorher bzw. am Ende entfernen. | Bei Unix-Sockets ist Entfernen am Ende Vorgabe. |
| `verify=0/1` | Zertifikatsprüfung bei `OPENSSL`. | Nicht abschalten. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Eine Nachricht über einen lokalen Unix-Socket in eine Datei schreiben – ganz ohne Netzwerk – und eine Datei kopieren.

### Schritt 1: Übungsordner

```bash
uebung="$(mktemp -d -t netmon-socat-XXXXXX)" || exit 1
cd "$uebung" || exit 1
```

### Schritt 2: Empfänger starten

```bash
timeout 10 socat -u UNIX-LISTEN:./sock OPEN:empfangen.txt,creat,wronly &
```

`socat` lauscht auf dem Socket `./sock` und schreibt Empfangenes in `empfangen.txt`. `-u` sorgt dafür, dass nur in diese Richtung gelesen wird.

### Schritt 3: Senden

```bash
printf 'Hallo socat\n' | socat -u - UNIX-CONNECT:./sock
```

### Schritt 4: Ergebnis

```bash
cat empfangen.txt
ls
```

`empfangen.txt` enthält `Hallo socat`. Die Socket-Datei ist danach verschwunden, weil `socat` sie laut Manpage beim Schließen entfernt.

Ohne `-u` meldete der Empfänger im Test `read(...): Bad file descriptor`, weil er versuchte, auch aus der nur zum Schreiben geöffneten Datei zu lesen; die Nachricht kam trotzdem an.

### Schritt 5: Datei kopieren

```bash
printf 'datei\n' > q.txt
socat -u FILE:q.txt CREATE:kopie.txt
cat kopie.txt
```

## 6. Typische Anwendungsfälle

- **Port-Weiterleitung:** einen lokalen Port an einen anderen Dienst weiterreichen.
- **Unix-Socket über TCP zugänglich machen** (vorsichtig, siehe Risiken).
- **Protokolle testen** mit `-v` als Mitschnitt.
- **Serielle Geräte** an ein Terminal oder Netz anbinden.
- **TLS-Tunnel** mit `OPENSSL`.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nicht zu. Der Kopf verwendet `caution`.

- **`EXEC:` und `SYSTEM:` an lauschenden Ports** machen ein Programm – im schlimmsten Fall eine Shell – über das Netz bedienbar. Nur mit `bind=127.0.0.1` oder `range=...` und mit Bedacht.
- **Weiterleitungen öffnen Zugänge:** Ein intern geschützter Dienst wird über `TCP-LISTEN` plötzlich von außen erreichbar.
- **Unverschlüsselt:** TCP- und UDP-Adressen übertragen im Klartext; `OPENSSL` mit `verify=0` schützt nicht vor Mittelsmännern.
- **Mitschnitte (`-v`, `-x`)** enthalten alle übertragenen Daten.
- **Dateien:** `CREATE` und `OPEN` mit `creat` können vorhandene Dateien überschreiben oder ergänzen.
- **Dauerprozesse mit `fork`** laufen weiter, bis sie beendet werden.

## 8. Häufige Fehler

| Meldung | Ursache | Vorgehen |
| --- | --- | --- |
| `E connect(...): No such file or directory` | Socket existiert nicht (im Test, Rückgabewert 1). | Empfänger zuerst starten. |
| `E read(...): Bad file descriptor` | Bidirektional auf ein reines Schreibziel. | `-u` verwenden. |
| `E bind(...): Address already in use` | Port oder Socket belegt. | Anderen Port, `unlink-early` bei Sockets. |
| `E connect(...): Connection refused` | Kein Dienst am Ziel. | Ziel prüfen. |
| Zertifikatsfehler bei `OPENSSL` | Ungültiges oder unbekanntes Zertifikat. | `cafile=` angeben statt `verify=0`. |

**Prüfpunkt:** Die letzten drei Zeilen wurden nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Mit Unix-Sockets und Dateien üben.**
2. **Lauschende Adressen mit `bind=127.0.0.1`.**
3. **Kein `EXEC`/`SYSTEM` an erreichbaren Ports.**
4. **`-u`, wenn nur eine Richtung gebraucht wird.**
5. **`socat`-Prozesse nach Tests beenden.**

### Prüfstand

- **Geprüfte Version:** socat 1.8.0.0 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie.
- **Tatsächlich ausgeführt** im Testordner: Unix-Socket-Empfänger mit und ohne `-u` (Nachricht kam an; ohne `-u` Lesefehler beim Empfänger), Socket-Datei nach Ende entfernt, Dateikopie mit `-u FILE: CREATE:`, Verbindung zu nicht vorhandenem Socket (Rückgabe 1), `socat -V`.
- **Nicht geprüft:** TCP-, UDP- und TLS-Adressen, `fork`, `EXEC`/`SYSTEM`, serielle Geräte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `nc`, `ncat` | Einfachere Werkzeuge für Netzwerkverbindungen. |
| `ssh -L`, `ssh -R` | Verschlüsselte Portweiterleitungen. |
| `openssl s_client` | TLS-Verbindungen testen. |
| `ss -ltnp` | Lauschende Ports und Prozesse anzeigen. |

Ausgangseintrag: Datensatz 167 in `index.json` (`socat`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch das Zwei-Adressen-Prinzip, Adresstypen, Optionen, Weiterleitungsrisiken und einen lokal geprüften Ablauf ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
