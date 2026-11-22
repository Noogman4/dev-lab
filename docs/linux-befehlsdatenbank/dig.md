---
id: "dig"
name: "dig"
command: "dig"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dns", "internet", "namensaufloesung", "fehlersuche"]
status: "Ausgearbeitet; Quellen geprüft; nur Hilfe und Version praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 153
reviewed_at: "2026-11-13"
locally_checked_version: "DiG 9.18.39 (Paket bind9-dnsutils 1:9.18.39-0ubuntu0.24.04.9)"
---

# dig – DNS-Server gezielt abfragen und Antworten genau anzeigen

## 1. Kurzbeschreibung

`dig` („domain information groper“) fragt **DNS-Server** ab und zeigt deren Antwort vollständig an: welche IP-Adresse zu einem Namen gehört, welche Mailserver eine Domain hat, welche Nameserver zuständig sind und vieles mehr. Laut [Debian-Manpage zu dig](https://manpages.debian.org/trixie/bind9-dnsutils/dig.1.en.html) ist es das Standardwerkzeug vieler DNS-Verwalter zur Fehlersuche.

**Root-Rechte sind nicht nötig.** `dig` sendet nur Anfragen und gibt die Antworten aus. Es verändert weder lokale Einstellungen noch DNS-Einträge.

## 2. Was macht der Befehl?

Ohne Serverangabe fragt `dig` die Server aus `/etc/resolv.conf`. Auf dem geprüften System steht dort `nameserver 127.0.0.53` – der lokale Zwischenspeicher von systemd-resolved, der die Anfrage weiterleitet. Ohne Typangabe wird ein `A`-Eintrag (IPv4-Adresse) abgefragt; ohne jedes Argument fragt `dig` die Nameserver der Wurzelzone ab.

Die Ausgabe ist in Abschnitte gegliedert: Kopf mit Status (`NOERROR`, `NXDOMAIN`, `SERVFAIL`), Frage, Antwort, gegebenenfalls Zusatzangaben und Statistik (Server, Antwortzeit, Größe).

Wichtig: `dig` verwendet nur DNS. Einträge aus `/etc/hosts` oder anderen Quellen der Namensauflösung des Systems berücksichtigt es nicht. Dafür ist `getent hosts NAME` geeignet.

## 3. Syntax

```text
dig [@SERVER] [NAME] [TYP] [KLASSE] [+ABFRAGEOPTIONEN]
dig -x ADRESSE
```

```bash
dig example.org
dig example.org MX +short
dig @9.9.9.9 example.org AAAA
dig -x 192.0.2.10
```

Das bisherige NetMon-Beispiel `dig --help` ist keine dokumentierte Option; die Manpage nennt `-h` für die Kurzhilfe. **Prüfpunkt:** Verhalten von `--help` nicht geprüft. Der Platzhalter `dig [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `@SERVER` | Bestimmten Nameserver fragen. | Zum Vergleich verschiedener Resolver. |
| `TYP` | Eintragstyp: `A`, `AAAA`, `MX`, `NS`, `TXT`, `SOA`, `CNAME` … | Vorgabe `A`. |
| `-x ADRESSE` | Rückwärtsauflösung (PTR). | IPv4 oder IPv6. |
| `-4`, `-6` | Nur IPv4 bzw. IPv6 als Transport. | – |
| `+short` | Nur die Antwortwerte. | Für Skripte. |
| `+noall +answer` | Nur den Antwortabschnitt anzeigen. | Übersichtlich. |
| `+trace` | Auflösung ab den Wurzelservern Schritt für Schritt. | Zeigt Delegationsfehler. |
| `+dnssec` | DNSSEC-Daten anfordern. | – |
| `+tcp` | TCP statt UDP. | – |
| `+norecurse` | Keine Rekursion anfordern. | Für autoritative Server. |
| `+timeout=S`, `+tries=N` | Zeitlimit (Vorgabe 5 s) und Versuche (Vorgabe 3). | – |
| `+search` | Suchliste aus `resolv.conf` verwenden. | Standardmäßig aus. |
| `-r` | `~/.digrc` nicht lesen. | Für vorhersagbare Skripte. |
| `-h` | Kurzhilfe. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Prüfen, ob eine Domain richtig auflöst und welcher Server antwortet. Das sendet DNS-Anfragen ins Netz; es ist ein **Beispielszenario** und wurde für dieses Dokument nicht ausgeführt.

### Schritt 1: Einfache Abfrage

```bash
dig example.org
```

Im Kopf steht `status: NOERROR`, im Abschnitt `ANSWER SECTION` die IPv4-Adresse, am Ende `SERVER: 127.0.0.53#53` und die Antwortzeit.

### Schritt 2: Kurzform für mehrere Typen

```bash
dig example.org A +short
dig example.org AAAA +short
dig example.org MX +short
```

### Schritt 3: Anderen Resolver vergleichen

```bash
dig @9.9.9.9 example.org +short
```

Unterscheiden sich die Antworten, liegt das Problem oft an einem Zwischenspeicher oder einer Filterung.

### Schritt 4: Delegation verfolgen

```bash
dig example.org +trace
```

Zeigt die Kette von den Wurzelservern über die Top-Level-Domain zu den zuständigen Nameservern.

## 6. Typische Anwendungsfälle

- **Webseite nicht erreichbar:** Löst der Name überhaupt auf?
- **E-Mail-Zustellung:** `MX`- und `TXT`-Einträge (SPF, DKIM) prüfen.
- **Nach DNS-Änderungen:** Autoritative Server mit `@SERVER +norecurse` direkt fragen.
- **DNS-Lecks und Filter erkennen:** Antwortenden Server in der Statistik beachten.
- **Rückwärtsauflösung** von IP-Adressen mit `-x`.

## 7. Risiken, Nebenwirkungen und Vorsicht

`dig` ist rein abfragend. Die ursprüngliche Einstufung „Grün – sicher lesend“ wird als `safe` übernommen. Hinweise:

- **Datenschutz:** Jede Abfrage verrät dem befragten Server (und möglicherweise Mitlesenden), welche Namen dich interessieren. Mit `@SERVER` umgehst du gegebenenfalls einen eingestellten, etwa VPN-geschützten Resolver.
- **Abweichung von der Systemauflösung:** Da `dig` `/etc/hosts` und andere Quellen ignoriert, kann es andere Ergebnisse liefern als Browser oder `ping`.
- **`+trace`** erzeugt viele Anfragen an verschiedene Server.
- **Zonenübertragung (`AXFR`)** bei fremden Servern ohne Erlaubnis zu versuchen, kann als Angriffsvorbereitung gewertet werden.

## 8. Häufige Fehler

| Beobachtung | Bedeutung | Vorgehen |
| --- | --- | --- |
| `status: NXDOMAIN` | Name existiert nicht. | Schreibweise prüfen. Rückgabewert trotzdem `0`. |
| `status: SERVFAIL` | Server konnte nicht auflösen, etwa DNSSEC-Fehler. | Anderen Resolver und `+trace` vergleichen. |
| `connection timed out; no servers could be reached` | Kein DNS-Server erreichbar. | Netz und `/etc/resolv.conf` prüfen; Rückgabewert `9`. |
| Leere Antwort mit `NOERROR` | Name existiert, aber nicht mit diesem Typ. | Anderen Typ abfragen. |
| Ergebnis weicht vom Browser ab | `/etc/hosts`, Zwischenspeicher oder DNS über HTTPS im Browser. | `getent hosts NAME` vergleichen. |

Rückgabewerte laut Manpage: `0` Antwort erhalten (auch bei NXDOMAIN), `1` Bedienfehler, `8` Stapeldatei nicht lesbar, `9` keine Antwort, `10` interner Fehler.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Mit `+short` beginnen.**
2. **Status im Kopf lesen,** nicht nur die Antwort.
3. **Für die Sicht des Systems `getent hosts`** zusätzlich verwenden.
4. **Fremde Resolver nur bewusst** mit `@` fragen.

### Prüfstand

- **Geprüfte Version:** DiG 9.18.39 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie.
- **Tatsächlich ausgeführt:** `dig -v`, `dig -h` und Lesen von `/etc/resolv.conf`. Es wurden bewusst **keine DNS-Anfragen** gesendet, um keine Netzwerk- oder DNS-Überwachung auszulösen.
- **Nicht geprüft:** alle Abfragen, Ausgabeformat im Detail, `+trace`, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `host` | Einfachere Ausgabe für schnelle Abfragen. |
| `nslookup` | Älteres, auch interaktives Abfragewerkzeug. |
| `getent hosts` | Namensauflösung wie das System sie durchführt. |
| `resolvectl query` | Abfrage über systemd-resolved mit dessen Einstellungen. |
| `whois` | Registrierungsdaten einer Domain. |

Ausgangseintrag: Datensatz 153 in `index.json` (`dig`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Abfrageaufbau, Ausgabeabschnitte, Abfrageoptionen, Rückgabewerte und Datenschutzhinweise ersetzt.
