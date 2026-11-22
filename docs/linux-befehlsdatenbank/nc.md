---
id: "nc"
name: "nc"
command: "nc"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "tcp", "udp", "sockets", "fehlersuche"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel mit Unix-Socket geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 159
reviewed_at: "2026-11-13"
locally_checked_version: "OpenBSD netcat 1.226 (Paket netcat-openbsd 1.226-1ubuntu2)"
---

# nc – Netzwerkverbindungen öffnen, lauschen und Ports prüfen (netcat)

## 1. Kurzbeschreibung

`nc` (netcat) ist ein vielseitiges Werkzeug für **TCP-, UDP- und Unix-Domain-Sockets**. Laut [Debian-Manpage zu nc.openbsd](https://manpages.debian.org/trixie/netcat-openbsd/nc.openbsd.1.en.html) kann es TCP-Verbindungen öffnen, UDP-Pakete senden, auf beliebigen Ports lauschen, Ports auf Erreichbarkeit prüfen und mit IPv4 und IPv6 arbeiten. Was über die Standardeingabe kommt, wird gesendet; was ankommt, erscheint auf der Standardausgabe.

**Root-Rechte sind meist nicht nötig.** Ausnahmen: Lauschen auf Ports unter 1024 und einige Sonderoptionen. Verbindungen zu fremden Rechnern brauchen keine besonderen Rechte.

### Welche Fassung?

Es gibt mehrere Implementierungen mit unterschiedlichen Optionen. Auf dem geprüften System zeigen `nc` und `netcat` über das Alternativen-System auf **OpenBSD netcat** (`/bin/nc.openbsd`). Die ältere „traditionelle“ Fassung (`nc.traditional`) kennt zusätzlich `-e` zum Ausführen eines Programms nach dem Verbindungsaufbau; die OpenBSD-Fassung hat diese Option nicht. Nmap liefert die eigene Variante `ncat`. Dieses Dokument beschreibt OpenBSD netcat.

## 2. Was macht der Befehl?

| Betriebsart | Aufruf | Wirkung |
| --- | --- | --- |
| Verbinden | `nc HOST PORT` | Baut eine TCP-Verbindung auf und leitet Ein- und Ausgabe weiter. |
| Lauschen | `nc -l PORT` | Wartet auf eine eingehende Verbindung. |
| Port prüfen | `nc -z HOST PORT` | Prüft nur, ob ein Dienst lauscht; sendet keine Daten. |
| UDP | `nc -u HOST PORT` | Sendet UDP-Pakete. |
| Unix-Socket | `nc -U PFAD` | Verbindet mit einem lokalen Socket; mit `-l` als Server. |

Laut Manpage trennt `nc` Fehlermeldungen sauber auf die Standardfehlerausgabe und eignet sich deshalb gut für Skripte.

## 3. Syntax

```text
nc [OPTIONEN] [ZIEL] [PORT]
nc -l [OPTIONEN] [ADRESSE] PORT
nc -U [-l] SOCKETPFAD
```

```bash
nc -zv example.org 443
nc -w 5 example.org 80
nc -lU /var/tmp/beispiel.sock
```

Das bisherige NetMon-Beispiel `nc --help` ist keine gültige Option von OpenBSD netcat; die Hilfe erscheint mit `nc -h`. Der Platzhalter `nc [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-l` | Lauschen statt verbinden. | Nicht mit `-x` oder `-z`; `-w` wird ignoriert. |
| `-k` | Nach einer Verbindung weiter lauschen. | Mit `-l`. |
| `-z` | Nur prüfen, ob Dienste lauschen. | Nicht mit `-l`. |
| `-v` | Ausführliche Meldungen. | Zeigt Erfolg oder Ablehnung bei `-z`. |
| `-w SEKUNDEN` | Zeitlimit für Verbindungsaufbau und letzte Lesevorgänge. | Für Skripte wichtig. |
| `-n` | Keine Namensauflösung. | – |
| `-u` | UDP statt TCP. | UDP ist verbindungslos; Erfolg lässt sich schwer erkennen. |
| `-U` | Unix-Domain-Socket. | Pfad statt Host und Port. |
| `-N` | Socket nach Ende der Eingabe schließen. | Manche Server brauchen das, um zu antworten. |
| `-q SEKUNDEN` | Nach Ende der Eingabe noch warten, dann beenden. | Nicht-negativ schließt `-N` ein. |
| `-C` | Zeilenende CRLF senden. | Für Protokolle wie SMTP oder HTTP. |
| `-p PORT`, `-s ADRESSE` | Lokalen Port bzw. Quelladresse festlegen. | – |
| `-x ADRESSE[:PORT]`, `-X PROTO` | Über Proxy verbinden (SOCKS 4/5 oder HTTP CONNECT). | Etwa für `ssh -o ProxyCommand`. |
| `-4`, `-6` | Nur IPv4 bzw. IPv6. | – |
| `-h` | Hilfe. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Eine Nachricht über einen **lokalen Unix-Domain-Socket** senden – ganz ohne Netzwerk. So lässt sich das Prinzip von Server und Client gefahrlos ausprobieren.

### Schritt 1: Übungsordner

```bash
uebung="$(mktemp -d -t netmon-nc-XXXXXX)" || exit 1
cd "$uebung" || exit 1
```

### Schritt 2: Server starten

```bash
timeout 10 nc -lU ./sock > empfangen.txt &
```

`nc` lauscht auf der Socket-Datei `./sock` und schreibt Empfangenes in `empfangen.txt`. `timeout` beendet den Server spätestens nach 10 Sekunden.

### Schritt 3: Nachricht senden

```bash
printf 'Hallo ueber Unix-Socket\n' | nc -N -U ./sock
```

`-N` schließt die Verbindung nach dem Senden.

### Schritt 4: Ergebnis prüfen

```bash
cat empfangen.txt
ls -l
```

`empfangen.txt` enthält die Nachricht. Im Test blieb die Socket-Datei `sock` nach dem Ende des Servers stehen (`srwxrwx---`); sie kann gelöscht werden.

### Übertragung auf TCP (nicht ausgeführt)

Mit `nc -zv HOST PORT` prüft man, ob ein Dienst erreichbar ist, etwa `nc -zv example.org 443`.

## 6. Typische Anwendungsfälle

- **Erreichbarkeit prüfen:** Ist ein Port offen oder blockiert eine Firewall?
- **Protokolle von Hand testen:** HTTP, SMTP oder eigene Dienste mit `-C`.
- **Dateien im lokalen Netz übertragen:** Empfänger `nc -l PORT > datei`, Sender `nc HOST PORT < datei` (unverschlüsselt).
- **Proxy-Verbindungen für SSH** mit `-x` und `-X`.
- **Lokale Sockets** von Diensten ansprechen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nicht zu: `nc` kann Ports öffnen, Daten senden und empfangen und Portscans durchführen. Der Kopf verwendet `caution`.

- **Offene Ports:** `nc -l` öffnet einen Port, über den jeder im Netz Daten senden kann. Ohne Firewall-Ausnahme bleibt er meist unerreichbar; mit Ausnahme ist er ungeschützt.
- **Unverschlüsselt:** Alles wird im Klartext übertragen.
- **Portscans** (`-z` über Portbereiche) gegen fremde Systeme können unzulässig sein und Sicherheitssysteme auslösen. Nur eigene oder ausdrücklich freigegebene Systeme prüfen.
- **Ausführen von Programmen:** Die traditionelle Fassung mit `-e` kann eine Shell an einen Port binden – ein klassischer Hintertürmechanismus. OpenBSD netcat bietet diese Option nicht.
- **Überschreiben:** Bei `nc -l ... > datei` wird die Zieldatei überschrieben.
- **Überwachung:** Lauschende Ports und ungewöhnliche Verbindungen fallen in Netzwerküberwachung auf.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `nc: ...: No such file or directory` | Socket-Pfad existiert nicht (im Test, Rückgabewert 1). | Pfad prüfen, Server zuerst starten. |
| `Connection refused` | Kein Dienst auf dem Port. | Port und Dienst prüfen. |
| Keine Antwort, Befehl hängt | Firewall verwirft Pakete oder Server wartet auf Eingabeende. | `-w` setzen, `-N` verwenden. |
| `Address already in use` | Port oder Socket-Datei belegt. | Anderen Port wählen; alte Socket-Datei löschen. |
| `nc: invalid option -- '-'` bei `--help` (im Test beobachtet) | OpenBSD netcat kennt keine langen Optionen. | `nc -h`. |
| Option `-e` unbekannt | OpenBSD-Fassung. | Bewusst so; nicht nachrüsten. |

**Prüfpunkt:** Außer der ersten Zeile wurden die Meldungen nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Mit Unix-Sockets oder `127.0.0.1` üben.**
2. **Immer `-w` setzen,** damit nichts hängen bleibt.
3. **Nur eigene Systeme scannen.**
4. **Für vertrauliche Daten `ssh`, `scp` oder `rsync`** statt `nc`.
5. **Lauschende `nc`-Prozesse nach dem Test beenden.**

### Prüfstand

- **Geprüfte Version:** OpenBSD netcat 1.226 (Ubuntu-Paket netcat-openbsd), über Alternativen als `nc` und `netcat`.
- **Tatsächlich ausgeführt** im Testordner: `nc -h`, `nc --help` (Fehlermeldung `invalid option`), Server und Client über einen Unix-Domain-Socket (Nachricht korrekt empfangen, Rückgabe 0, Socket-Datei blieb liegen), Verbindungsversuch zu nicht vorhandenem Socket (Rückgabe 1).
- **Nicht geprüft:** jede TCP- oder UDP-Verbindung, `-z`, Proxys, Lauschen auf Netzwerkports.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `netcat` | Auf dem geprüften System derselbe Befehl. |
| `ncat` | Netcat-Variante von Nmap mit TLS und Zugriffskontrollen. |
| `socat` | Deutlich vielseitigeres Werkzeug für Datenkanäle. |
| `ss -ltn` | Zeigt lauschende Ports auf dem eigenen Rechner. |
| `telnet` | Älteres Werkzeug für interaktive Textverbindungen. |

Ausgangseintrag: Datensatz 159 in `index.json` (`nc`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Implementierungsunterschiede, Betriebsarten, Optionen, Risiken und einen lokal geprüften Ablauf ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
