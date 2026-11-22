---
id: "host"
name: "host"
command: "host"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dns", "internet", "namensaufloesung"]
status: "Ausgearbeitet; Quellen geprüft; nur Hilfe und Version praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 156
reviewed_at: "2026-11-13"
locally_checked_version: "host 9.18.39 (Paket bind9-host 1:9.18.39-0ubuntu0.24.04.9)"
---

# host – Namen und IP-Adressen schnell per DNS auflösen

## 1. Kurzbeschreibung

`host` ist laut [Debian-Manpage zu host](https://manpages.debian.org/trixie/bind9-host/host.1.en.html) ein einfaches Werkzeug für **DNS-Abfragen**. Es wandelt Namen in IP-Adressen um und umgekehrt und gibt das Ergebnis in knappen, gut lesbaren Sätzen aus, etwa `example.org has address 192.0.2.10`.

**Root-Rechte sind nicht nötig.** `host` sendet nur Anfragen.

`host` stammt wie `dig` und `nslookup` aus dem BIND-Projekt. Es ist knapper als `dig` und eignet sich für schnelle Prüfungen.

## 2. Was macht der Befehl?

- `host NAME` fragt ohne Typangabe automatisch mehrere Einträge ab. Laut aktueller Debian-Manpage sind das `A`, `AAAA`, `MX` und `HTTPS`. **Prüfpunkt:** Die lokal installierte Version 9.18 kann eine kleinere Auswahl abfragen; nicht geprüft.
- `host IP-ADRESSE` führt automatisch eine **Rückwärtsauflösung** (PTR) durch.
- Ohne Serverangabe nutzt `host` die Server aus `/etc/resolv.conf`; ein zweites Argument wählt einen anderen Server.
- Ohne Argumente gibt `host` eine Kurzhilfe aus.

Wie `dig` verwendet `host` nur DNS; Einträge aus `/etc/hosts` erscheinen nicht.

## 3. Syntax

```text
host [OPTIONEN] NAME [SERVER]
```

```bash
host example.org
host -t MX example.org
host 192.0.2.10
host example.org 9.9.9.9
```

Das bisherige NetMon-Beispiel `host --help` ist keine dokumentierte Option. Die Kurzhilfe erscheint, wenn `host` ohne Argumente aufgerufen wird (Rückgabewert `1` im Test). Der Platzhalter `host [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-t TYP` | Bestimmten Typ abfragen: `A`, `AAAA`, `MX`, `NS`, `TXT`, `SOA`, `CNAME` … | – |
| `-a` | Alles ausführlich (`-v -t ANY`). | Viele Server beantworten `ANY` nur eingeschränkt. |
| `-v`, `-d` | Ausführliche Ausgabe wie bei `dig`. | – |
| `-C` | SOA aller autoritativen Server vergleichen. | Prüft Konsistenz einer Zone. |
| `-r` | Keine Rekursion anfordern. | Für autoritative Server. |
| `-T`, `-U` | TCP bzw. UDP. | – |
| `-4`, `-6` | Nur IPv4 bzw. IPv6 als Transport. | – |
| `-W SEKUNDEN` | Wartezeit auf Antwort. | Mindestens 1 s. |
| `-R ANZAHL` | Wiederholungen bei UDP. | – |
| `-p PORT` | Anderer Port (Vorgabe 53). | – |
| `-l` | Zonenübertragung (AXFR) anfordern. | Nur bei eigenen Servern sinnvoll. |
| `-V` | Version. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Adresse, Mailserver und Rückwärtsauflösung einer Domain prüfen. Das sendet DNS-Anfragen; es ist ein **Beispielszenario** und wurde für dieses Dokument nicht ausgeführt.

### Schritt 1: Adressen

```bash
host example.org
```

Ausgabe in Sätzen wie `example.org has address ...` und `example.org has IPv6 address ...`, gegebenenfalls `... mail is handled by ...`.

### Schritt 2: Nur Mailserver

```bash
host -t MX example.org
```

### Schritt 3: Rückwärts

```bash
host 192.0.2.10
```

Zeigt `... domain name pointer NAME.` oder `not found: 3(NXDOMAIN)`, wenn kein PTR-Eintrag existiert.

### Schritt 4: Anderen Resolver fragen

```bash
host example.org 9.9.9.9
```

Die Ausgabe nennt zuerst den verwendeten Server.

## 6. Typische Anwendungsfälle

- **Schneller Test,** ob ein Name auflöst.
- **Mailserver einer Domain** anzeigen.
- **IP-Adressen in Protokollen** einem Namen zuordnen.
- **Zonenkonsistenz** mit `-C` nach Änderungen prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

`host` ist rein abfragend. Die ursprüngliche Einstufung „Grün – sicher lesend“ wird als `safe` übernommen. Hinweise:

- **Datenschutz:** Der befragte Server erfährt die angefragten Namen; ein zweites Argument umgeht unter Umständen einen geschützten Resolver.
- **Abweichung vom System:** `/etc/hosts` und andere Quellen werden nicht berücksichtigt.
- **`-l` (AXFR)** gegen fremde Server ohne Erlaubnis kann als Angriffsvorbereitung gelten.

## 8. Häufige Fehler

| Beobachtung | Bedeutung | Vorgehen |
| --- | --- | --- |
| `Host ... not found: 3(NXDOMAIN)` | Name existiert nicht. | Schreibweise prüfen. |
| `Host ... not found: 2(SERVFAIL)` | Server konnte nicht auflösen. | Anderen Resolver probieren. |
| `connection timed out; no servers could be reached` | Kein DNS-Server erreichbar. | Netz und `/etc/resolv.conf` prüfen. |
| Kurzhilfe statt Ergebnis | Kein Name angegeben oder unbekannte Option. | Aufruf prüfen. |

**Prüfpunkt:** Die Meldungstexte sind sinngemäß wiedergegeben und nicht praktisch ausgelöst; lokal geprüft wurde nur der Aufruf ohne Argumente (Kurzhilfe, Rückgabewert 1).

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **`host` für schnelle Prüfungen,** `dig` für Details.
2. **Mit `-t` gezielt** den gewünschten Typ abfragen.
3. **Für die Systemsicht** zusätzlich `getent hosts NAME`.

### Prüfstand

- **Geprüfte Version:** host 9.18.39 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie.
- **Tatsächlich ausgeführt:** `host -V` (Rückgabe 0) und `host` ohne Argumente (Kurzhilfe, Rückgabe 1). Es wurden bewusst **keine DNS-Anfragen** gesendet.
- **Nicht geprüft:** alle Abfragen, Standardtypen der lokalen Version, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `dig` | Ausführliche DNS-Abfragen mit vollständiger Antwort. |
| `nslookup` | Älteres, auch interaktives Werkzeug. |
| `getent hosts` | Auflösung wie das System sie durchführt. |
| `resolvectl query` | Abfrage über systemd-resolved. |

Ausgangseintrag: Datensatz 156 in `index.json` (`host`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Funktionsweise, Optionen, typische Ausgaben und Datenschutzhinweise ersetzt; `--help` wurde als nicht dokumentiert gekennzeichnet.
