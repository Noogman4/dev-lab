---
id: "gnutls_cli"
name: "gnutls-cli"
command: "gnutls-cli"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dns", "internet", "tls", "zertifikate", "fehlersuche"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 155
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert (Paket gnutls-bin fehlt); nicht praktisch geprüft"
---

# gnutls-cli – TLS-Verbindungen testen und Serverzertifikate prüfen

## 1. Kurzbeschreibung

`gnutls-cli` ist ein einfacher **TLS-Client** aus der GnuTLS-Bibliothek. Laut [Debian-Manpage zu gnutls-cli](https://manpages.debian.org/trixie/gnutls-bin/gnutls-cli.1.en.html) baut er eine TLS-Verbindung zu einem anderen Rechner auf und leitet Daten von der Standardeingabe an die gesicherte Verbindung weiter und umgekehrt. Damit lassen sich Zertifikate, TLS-Versionen und Verschlüsselungsverfahren eines Servers prüfen oder Protokolle wie HTTP oder SMTP von Hand über TLS sprechen.

**Root-Rechte sind nicht nötig.**

Auf dem geprüften System ist das Paket `gnutls-bin` nicht installiert.

## 2. Was macht der Befehl?

`gnutls-cli HOST -p PORT` löst den Namen auf, verbindet sich, führt den TLS-Handshake durch und zeigt dabei Informationen an: Zertifikatskette, Gültigkeit, ausgehandelte TLS-Version, Schlüsselaustausch und Verschlüsselung. Nach dem Handshake ist die Verbindung interaktiv: Was du eintippst, geht verschlüsselt an den Server; seine Antwort erscheint im Terminal.

Standardmäßig wird das Serverzertifikat geprüft. Schlägt die Prüfung fehl, bricht `gnutls-cli` ab, außer mit `--insecure`.

Mit `--starttls-proto` beherrscht es Dienste, die zunächst unverschlüsselt beginnen und dann auf TLS umschalten (etwa SMTP auf Port 25 oder 587, IMAP, POP3, LDAP, XMPP, PostgreSQL).

## 3. Syntax

```text
gnutls-cli [OPTIONEN] HOSTNAME
```

```bash
gnutls-cli -p 443 example.org
gnutls-cli --starttls-proto smtp -p 25 mail.example.org
gnutls-cli --priority SECURE192 -l
```

Das bisherige NetMon-Beispiel `gnutls-cli --help` ist gültig (`-h`, `--help` laut Manpage). Der Platzhalter `gnutls-cli [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-p PORT`, `--port` | Port oder Dienstname. | Etwa `443` oder `https`. |
| `--starttls-proto=PROTO` | STARTTLS für `smtp`, `imap`, `pop3`, `ldap`, `xmpp`, `ftp`, `postgres` u. a. | Nicht mit `--starttls` kombinieren. |
| `-s`, `--starttls` | Erst unverschlüsselt verbinden, TLS später auslösen. | – |
| `--print-cert` | Serverzertifikat im PEM-Format ausgeben. | – |
| `--save-cert=DATEI` | Zertifikatskette speichern. | – |
| `--x509cafile=DATEI` | Eigene Zertifizierungsstelle verwenden. | Für interne Dienste. |
| `--sni-hostname=NAME` | Namen für SNI festlegen. | Bei Tests unter anderem DNS-Namen. |
| `--verify-hostname=NAME` | Namen für die Zertifikatsprüfung festlegen. | – |
| `--ocsp` | Zertifikatsstatus per OCSP prüfen. | – |
| `--tofu`, `--strict-tofu` | Vertrauen beim ersten Kontakt, ähnlich SSH. | `--strict-tofu` bricht bei geänderten Schlüsseln ab. |
| `--priority=TEXT` | Erlaubte Verfahren, etwa `NORMAL` (Vorgabe), `SECURE256`. | – |
| `-l`, `--list` | Unterstützte Verfahren auflisten. | Mit `--priority` gefiltert. |
| `--alpn=PROTO` | ALPN aushandeln, etwa `h2`. | – |
| `--crlf` | CR LF statt LF senden. | Für Textprotokolle wie SMTP. |
| `--insecure` | Bei ungültigem Zertifikat nicht abbrechen. | Nur zur Diagnose. |
| `--logfile=DATEI` | Infomeldungen umleiten. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Prüfen, welches Zertifikat ein Webserver liefert und ob die Prüfung gelingt. Das baut eine Netzwerkverbindung auf; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Verbindung aufbauen

```bash
gnutls-cli -p 443 example.org
```

Die Ausgabe zeigt die Zertifikate der Kette mit Inhaber, Aussteller und Gültigkeit, das Prüfergebnis sowie TLS-Version und Verfahren. Danach wartet die Verbindung auf Eingaben.

### Schritt 2: Eine HTTP-Anfrage von Hand senden

```text
HEAD / HTTP/1.1
Host: example.org

```

Nach der Leerzeile antwortet der Server mit seinen Kopfzeilen. Beenden mit Strg+D.

### Schritt 3: Zertifikat speichern

```bash
gnutls-cli -p 443 --save-cert=kette.pem example.org < /dev/null
```

`< /dev/null` beendet die Verbindung direkt nach dem Handshake.

## 6. Typische Anwendungsfälle

- **Zertifikatsfehler eingrenzen:** abgelaufen, falscher Name, unvollständige Kette.
- **Mailserver prüfen:** `--starttls-proto smtp`.
- **TLS-Konfiguration bewerten:** welche Version und welche Verfahren ein Server aushandelt.
- **Interne Dienste mit eigener CA** über `--x509cafile` testen.

## 7. Risiken, Nebenwirkungen und Vorsicht

`gnutls-cli` verändert lokal nichts, außer beim Speichern mit `--save-cert` oder `--logfile`. Die ursprüngliche Einstufung „Grün – sicher lesend“ wird als `safe` übernommen. Zu beachten:

- **`--insecure`** nicht für echte Datenübertragung verwenden; Abhören und Manipulation werden möglich.
- **Eingaben gehen an den Server:** Was du im interaktiven Teil tippst, wird gesendet – auch Zugangsdaten bei Protokollen wie SMTP oder IMAP.
- **`--tofu`** speichert Schlüssel in einer lokalen Datei. **Prüfpunkt:** Speicherort nicht in der Manpage-Passage angegeben.
- **Fremde Server testen:** Viele Verbindungen oder Prüfungen gegen fremde Systeme können als Angriff gewertet werden.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `gnutls-cli: command not found` | Paket `gnutls-bin` fehlt. | Paket installieren lassen. |
| Zertifikatsprüfung schlägt fehl | Abgelaufen, falscher Name, fehlende Zwischenzertifikate oder unbekannte CA. | Kette mit `--print-cert` ansehen. |
| Handshake scheitert | Kein gemeinsames Verfahren oder kein TLS auf diesem Port. | Port, `--starttls-proto` und `--priority` prüfen. |
| Server antwortet nicht auf Eingaben | Zeilenende falsch. | `--crlf` verwenden. |

Laut Manpage endet `gnutls-cli` mit `0` bei Erfolg und `1` bei Fehlern oder ungültiger Syntax. **Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Ohne `--insecure` arbeiten;** ein Abbruch ist das gewünschte Warnsignal.
2. **Mit `< /dev/null`** nur den Handshake prüfen.
3. **Für STARTTLS-Dienste `--starttls-proto`** verwenden.
4. **Zum Vergleich `openssl s_client`** heranziehen.

### Prüfstand

- **Geprüfte Version:** keine; `gnutls-cli` ist nicht installiert. Die Debian-Manpage beschreibt GnuTLS 3.8.9.
- **Quellen gelesen:** Debian-Manpage `gnutls-cli(1)` (Beschreibung, Optionen, Beispiele, Exit-Status), Abruf 2026-11-13.
- **Nicht geprüft:** alle Verbindungen, Ausgabeformat, TOFU-Speicher, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `openssl s_client` | Entsprechendes Werkzeug aus OpenSSL. |
| `gnutls-cli-debug` | Prüft, welche TLS-Funktionen ein Server unterstützt. |
| `gnutls-serv` | Einfacher TLS-Testserver aus demselben Paket (laut SEE ALSO der Manpage). |
| `curl -v` | Zeigt TLS-Details bei HTTP-Abrufen. |

Ausgangseintrag: Datensatz 155 in `index.json` (`gnutls-cli`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Verbindungsablauf, Zertifikatsprüfung, STARTTLS, Optionen und einen Prüfablauf ersetzt.
