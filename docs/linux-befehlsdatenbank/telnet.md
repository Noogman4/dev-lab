---
id: "telnet"
name: "telnet"
command: "telnet"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "tcp", "fernzugriff", "fehlersuche"]
status: "Ausgearbeitet; Quellen geprüft; nur Hilfe und Version praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 174
reviewed_at: "2026-11-13"
locally_checked_version: "telnet (GNU inetutils) 2.5 (Paket inetutils-telnet 2:2.5-3ubuntu4.2)"
---

# telnet – Unverschlüsselte Textverbindung zu einem Rechner oder Port

## 1. Kurzbeschreibung

`telnet` verbindet sich über das **TELNET-Protokoll** mit einem anderen Rechner. Früher diente es zur Fernanmeldung; heute ist dafür `ssh` Standard, weil `telnet` **alles unverschlüsselt** überträgt – auch Passwörter. Praktisch wird `telnet` noch verwendet, um zu prüfen, ob ein TCP-Port erreichbar ist, oder um Textprotokolle (SMTP, HTTP) von Hand zu testen, sowie für ältere Netzwerkgeräte.

**Root-Rechte sind nicht nötig.**

### Welche Fassung?

Auf dem geprüften System zeigt `telnet` über das Alternativen-System auf **GNU inetutils telnet** (`/usr/bin/inetutils-telnet`). Daneben gibt es unter Debian weitere Fassungen (etwa das Paket `telnet-ssl`). Dieses Dokument folgt der [Debian-Manpage zu inetutils-telnet](https://manpages.debian.org/trixie/inetutils-telnet/inetutils-telnet.1.en.html) und der lokalen Hilfe.

## 2. Was macht der Befehl?

- `telnet HOST [PORT]` öffnet eine Verbindung (Vorgabe: TELNET-Port 23) und leitet Tastatureingaben weiter.
- Ohne Host startet laut Manpage der **Befehlsmodus** mit der Eingabeaufforderung `telnet>`.
- Aus einer laufenden Verbindung gelangt man mit dem **Escape-Zeichen** in den Befehlsmodus; anfangs `Strg+]` (in der Manpage `^]`). Dort beendet `close` die Verbindung, `quit` das Programm.

Verbindet man sich mit einem anderen Port als 23 (etwa 25 oder 80), spricht man direkt mit dem dortigen Dienst. Ein erfolgreicher Verbindungsaufbau zeigt, dass der Port erreichbar ist.

## 3. Syntax

```text
telnet [OPTIONEN] [HOST [PORT]]
```

```bash
telnet mail.example.org 25
telnet 192.0.2.10 80
telnet
```

Das bisherige NetMon-Beispiel `telnet --help` funktioniert bei GNU inetutils und zeigt die Optionsübersicht (im Test geprüft). Der Platzhalter `telnet [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-4`, `-6` | Nur IPv4 bzw. IPv6. | – |
| `-e ZEICHEN`, `--escape` | Anderes Escape-Zeichen. | Ohne Zeichen: keines. |
| `-E`, `--no-escape` | Kein Escape-Zeichen. | Dann kein Wechsel in den Befehlsmodus möglich. |
| `-l BENUTZER` | Automatische Anmeldung als Benutzer versuchen. | – |
| `-K` | Keine automatische Anmeldung. | – |
| `-8`, `-L` | 8-Bit-Übertragung (beidseitig bzw. nur Ausgabe). | – |
| `-b ADRESSE` | Lokale Adresse binden. | – |
| `-c` | `~/.telnetrc` nicht lesen. | – |
| `-n DATEI` | Ablaufprotokoll in Datei schreiben. | – |
| `-x` | Verschlüsselung, falls möglich. | Hängt von Gegenstelle ab. **Prüfpunkt:** nicht geprüft. |
| `-?`, `--help`, `-V` | Hilfe, Version. | – |

Befehle im Befehlsmodus (Auswahl): `open HOST [PORT]`, `close`, `status`, `send`, `quit`.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Prüfen, ob ein Webserver auf Port 80 erreichbar ist, und eine HTTP-Anfrage von Hand senden. Das baut eine Netzwerkverbindung auf; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Verbinden

```bash
telnet example.org 80
```

Erscheinen `Connected to …` und ein Hinweis auf das Escape-Zeichen, ist der Port erreichbar.

### Schritt 2: Anfrage eingeben

```text
HEAD / HTTP/1.1
Host: example.org

```

Nach der Leerzeile antwortet der Server mit Statuszeile und Kopfzeilen.

### Schritt 3: Beenden

`Strg+]` drücken, dann `quit` eingeben.

## 6. Typische Anwendungsfälle

- **Portprüfung** bei Firewall- oder Dienstproblemen.
- **Textprotokolle testen:** SMTP, POP3, HTTP (ohne TLS).
- **Ältere Netzwerkgeräte** (Switches, Router, serielle Konsolenserver), die nur TELNET anbieten – möglichst nur in abgeschotteten Verwaltungsnetzen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ wird nicht übernommen. Der Kopf verwendet `caution`.

- **Klartext:** Benutzernamen, Passwörter und alle Inhalte können im Netz mitgelesen werden. Für Anmeldungen `ssh` verwenden.
- **Unverschlüsselte Geräteverwaltung** nur in vertrauenswürdigen, getrennten Netzen.
- **Eingaben gehen direkt an den Dienst:** Bei Mail- oder Datenbankdiensten können Befehle tatsächlich etwas auslösen.
- **Fremde Systeme prüfen** nur mit Erlaubnis.
- **TLS-Dienste** (HTTPS, SMTPS) lassen sich mit `telnet` nicht sinnvoll testen; dafür `openssl s_client` oder `gnutls-cli`.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `Connection refused` | Kein Dienst auf dem Port. | Port und Dienst prüfen. |
| Hängt bei `Trying …` | Firewall verwirft Pakete oder falsche Adresse. | Mit Strg+C abbrechen; Netz prüfen. |
| Verbindung lässt sich nicht beenden | Escape-Zeichen unbekannt. | `Strg+]`, dann `quit`. |
| Wirre Zeichen | Gegenstelle spricht TLS oder ein Binärprotokoll. | Passendes Werkzeug verwenden. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Für Fernanmeldungen `ssh`,** nie `telnet` über das Internet.
2. **Für reine Portprüfungen `nc -zv HOST PORT`** – ohne interaktive Sitzung.
3. **Escape-Zeichen merken:** `Strg+]`.
4. **Für TLS `openssl s_client`.**

### Prüfstand

- **Geprüfte Version:** telnet aus GNU inetutils 2.5 (Ubuntu 24.04-Basis), über Alternativen eingerichtet.
- **Tatsächlich ausgeführt:** `telnet --help`, `telnet --version`, Ermittlung der Implementierung über die Verweise.
- **Nicht geprüft:** jede Verbindung, Befehlsmodus, Verschlüsselung, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ssh` | Verschlüsselter Ersatz für Fernanmeldungen. |
| `nc`, `ncat`, `socat` | Flexiblere Werkzeuge für TCP-Verbindungen. |
| `openssl s_client`, `gnutls-cli` | Textprotokolle über TLS testen. |

Ausgangseintrag: Datensatz 174 in `index.json` (`telnet`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Implementierung, Befehlsmodus, heutige Einsatzzwecke und die Klartext-Risiken ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
