---
id: "ncat"
name: "ncat"
command: "ncat"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "tcp", "tls", "nmap", "fehlersuche"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 160
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert (Paket ncat fehlt); nicht praktisch geprüft"
---

# ncat – Netcat aus dem Nmap-Projekt mit TLS, Proxys und Zugriffskontrolle

## 1. Kurzbeschreibung

`ncat` ist eine Weiterentwicklung von netcat aus dem **Nmap-Projekt**. Laut [Debian-Manpage zu ncat](https://manpages.debian.org/trixie/ncat/ncat.1.en.html) liest und schreibt es Daten über Netzwerkverbindungen und bietet dabei mehr als klassisches `nc`: **TLS-Verschlüsselung**, Proxys (SOCKS4, SOCKS5, HTTP), Weiterleitungen, Verbindungsvermittlung („broker“), einen einfachen Chat-Modus, Zugriffslisten und das Ausführen von Programmen bei eingehenden Verbindungen.

**Root-Rechte sind meist nicht nötig.** Ausnahmen sind etwa Lauschen auf Ports unter 1024.

Auf dem geprüften System ist `ncat` nicht installiert; `nc` und `netcat` verweisen dort auf OpenBSD netcat.

## 2. Was macht der Befehl?

Wie `nc` arbeitet `ncat` im **Verbindungsmodus** (`ncat HOST PORT`) oder im **Lauschmodus** (`ncat -l PORT`). Ein lauschender Server nimmt laut Manpage normalerweise **eine** Verbindung an und beendet sich danach; mit `-k` nimmt er mehrere an (Vorgabe höchstens 100 gleichzeitig, `-m`).

Besonderheiten gegenüber OpenBSD netcat:

| Funktion | Option |
| --- | --- |
| TLS als Client oder Server | `--ssl`, `--ssl-verify`, `--ssl-trustfile`, `--ssl-cert`, `--ssl-key` |
| Programme an Verbindungen binden | `-e`, `-c`, `--lua-exec` |
| Zugriff steuern | `--allow`, `--deny` |
| Mehrere Teilnehmer verbinden | `--broker`, `--chat` |
| Sitzung mitschneiden | `-o`, `-x` (Hex) |
| Proxy | `--proxy`, `--proxy-type`, `--proxy-auth` |

**Wichtig zu TLS:** `--ssl` verschlüsselt, prüft aber laut Manpage das Serverzertifikat nicht; erst `--ssl-verify` verlangt eine gültige Zertifikatsprüfung.

## 3. Syntax

```text
ncat [OPTIONEN] [HOST] [PORT]
ncat -l [OPTIONEN] [ADRESSE] [PORT]
```

```bash
ncat -zv example.org 443
ncat --ssl-verify example.org 443
ncat -l 127.0.0.1 9000 --allow 127.0.0.1
```

Das bisherige NetMon-Beispiel `ncat --help` ist gültig (`-h`, `--help` laut Manpage). Der Platzhalter `ncat [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-l`, `--listen` | Lauschen. | – |
| `-k`, `--keep-open` | Mehrere Verbindungen annehmen. | Nur mit `-l`. |
| `-m N`, `--max-conns` | Höchstzahl gleichzeitiger Verbindungen. | Vorgabe 100. |
| `-z` | Nur Verbindungsstatus melden. | Für Erreichbarkeitsprüfungen. |
| `-w ZEIT`, `--wait` | Zeitlimit für den Verbindungsaufbau. | – |
| `-u`, `--udp`; `--sctp`; `-U` | UDP, SCTP bzw. Unix-Domain-Socket. | – |
| `--ssl` | TLS verwenden. | Ohne Zertifikatsprüfung. |
| `--ssl-verify` | TLS mit Zertifikatsprüfung. | Für echte Verbindungen. |
| `--ssl-trustfile DATEI` | Eigene vertrauenswürdige Zertifikate. | Nur mit `--ssl-verify` wirksam. |
| `--allow`, `--deny` | Zulässige bzw. abgelehnte Gegenstellen. | `--allow` hat Vorrang. |
| `--send-only`, `--recv-only` | Nur senden bzw. nur empfangen. | – |
| `-o DATEI`, `-x DATEI` | Sitzung als Text bzw. Hex speichern. | Enthält alle übertragenen Daten. |
| `-e BEFEHL`, `-c BEFEHL` | Programm nach Verbindungsaufbau ausführen. | Siehe Abschnitt 7. |
| `--proxy HOST[:PORT]` | Über Proxy verbinden. | Vorgabeports 1080 (SOCKS) bzw. 3128 (HTTP). |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Eine TLS-Verbindung zu einem Webserver mit Zertifikatsprüfung aufbauen und eine Kopfzeilen-Anfrage senden. Das braucht Netzwerkzugang; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Verbindung mit Prüfung

```bash
ncat --ssl-verify -C example.org 443
```

`-C` (`--crlf`) sendet laut Optionsübersicht der Manpage CRLF als Zeilenende, wie HTTP es verlangt.

### Schritt 2: Anfrage eingeben

```text
HEAD / HTTP/1.1
Host: example.org

```

Der Server antwortet mit Statuszeile und Kopfzeilen. Beenden mit Strg+D.

### Schritt 3: Rückgabewert

```bash
echo $?
```

Laut Manpage: `0` ohne Fehler, `1` Netzwerkfehler (etwa „Connection refused“), `2` andere Fehler wie ungültige Optionen.

## 6. Typische Anwendungsfälle

- **TLS-Dienste von Hand testen.**
- **Eingeschränkte Testserver** mit `--allow 127.0.0.1`.
- **Port-Weiterleitung oder Verbindung über Proxys.**
- **Mitschnitt einer Sitzung** zur Fehlersuche mit `-o`/`-x`.
- **Erreichbarkeit prüfen** mit `-z`.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nicht zu. Der Kopf verwendet `caution`.

- **`-e`, `-c`, `--lua-exec`** binden ein Programm an eine Netzverbindung. Mit `-l` und einer Shell entsteht eine Fernsteuerung für jeden, der den Port erreicht. Die Manpage warnt in diesem Zusammenhang vor Sicherheitslücken; ohne `--allow` niemals so einsetzen.
- **`--ssl` ohne Prüfung** schützt nicht vor Abhören durch einen Mittelsmann. `--ssl-verify` verwenden.
- **Offene Ports** mit `-l -k` bleiben dauerhaft erreichbar.
- **Mitschnitte** (`-o`, `-x`) enthalten alle Daten, auch Passwörter.
- **Scans fremder Systeme** nur mit Erlaubnis.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `ncat: command not found` | Paket `ncat` fehlt. | Paket installieren lassen. |
| Rückgabewert `1`, „Connection refused“ | Kein Dienst auf dem Port. | Port prüfen. |
| Rückgabewert `2` | Ungültige Option oder fehlende Datei. | Aufruf prüfen. |
| Zertifikatsfehler mit `--ssl-verify` | Ungültiges oder unbekanntes Zertifikat. | Kette prüfen, ggf. `--ssl-trustfile`. |
| Server beendet sich nach einer Verbindung | Ohne `-k`. | `-k` ergänzen. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **TLS nur mit `--ssl-verify`.**
2. **Lauschende Server an `127.0.0.1` binden** und mit `--allow` begrenzen.
3. **Kein `-e`/`-c` an offenen Ports.**
4. **Testserver nach Gebrauch beenden.**

### Prüfstand

- **Geprüfte Version:** keine; `ncat` ist nicht installiert.
- **Quellen gelesen:** Debian-Manpage `ncat(1)` (Beschreibung, Optionen, Exit-Codes), Abruf 2026-11-13.
- **Nicht geprüft:** alle Verbindungen, TLS-Verhalten, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `nc`, `netcat` | Schlankere netcat-Fassungen. |
| `nmap` | Portscanner desselben Projekts. |
| `socat` | Universelles Werkzeug für Datenkanäle, auch mit TLS. |
| `openssl s_client`, `gnutls-cli` | Spezialisierte TLS-Clients. |

Ausgangseintrag: Datensatz 160 in `index.json` (`ncat`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch die Abgrenzung zu netcat, TLS-Prüfung, Zugriffskontrolle, Programmausführung und Exit-Codes ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
