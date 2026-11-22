---
id: "nslookup"
name: "nslookup"
command: "nslookup"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dns", "internet", "namensaufloesung"]
status: "Ausgearbeitet; Quellen geprüft; nur Version und Fehlbedienung praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 162
reviewed_at: "2026-11-13"
locally_checked_version: "nslookup 9.18.39 (Paket bind9-dnsutils 1:9.18.39-0ubuntu0.24.04.9)"
---

# nslookup – DNS-Server abfragen, auch im interaktiven Modus

## 1. Kurzbeschreibung

`nslookup` fragt **DNS-Server** nach Informationen zu Namen und IP-Adressen. Laut [Debian-Manpage zu nslookup](https://manpages.debian.org/trixie/bind9-dnsutils/nslookup.1.en.html) kennt es zwei Betriebsarten: einen **nicht-interaktiven** Modus für einzelne Abfragen und einen **interaktiven** Modus mit eigener Eingabeaufforderung (`>`), in dem nacheinander mehrere Abfragen gestellt und Einstellungen geändert werden.

**Root-Rechte sind nicht nötig.** `nslookup` sendet nur Anfragen.

`nslookup` ist auch unter Windows verbreitet; viele Anleitungen nutzen es deshalb plattformübergreifend. Unter Linux bietet `dig` mehr Details, `host` die knappere Ausgabe.

## 2. Was macht der Befehl?

- **Nicht-interaktiv:** `nslookup NAME [SERVER]` gibt Name und angefragte Information aus. Laut Manpage werden ohne Typangabe `A` und danach `AAAA` abgefragt.
- **Interaktiv:** Ohne Argumente oder mit `-` als erstem Argument startet die Eingabeaufforderung.
- Ohne Serverangabe wird der Server aus `/etc/resolv.conf` verwendet; auf dem geprüften System ist das `127.0.0.53` (systemd-resolved).
- Die Ausgabe unterscheidet zwischen „Non-authoritative answer“ (aus einem Zwischenspeicher) und Antworten der zuständigen Server. **Prüfpunkt:** Wortlaut nicht praktisch geprüft.

Laut Manpage sind einige ältere interaktive Befehle wie `ls`, `finger`, `root`, `view` sowie `help` und `?` in dieser Fassung **nicht implementiert**.

## 3. Syntax

```text
nslookup [-OPTION=WERT ...] NAME [SERVER]
nslookup [-OPTION=WERT ...] - [SERVER]
nslookup
```

```bash
nslookup example.org
nslookup -type=MX example.org
nslookup 192.0.2.10
nslookup example.org 9.9.9.9
```

Das bisherige NetMon-Beispiel `nslookup --help` funktioniert nicht: Im Test meldete `nslookup` `*** Invalid option: -help`. Die Versionsanzeige heißt `nslookup -version`; eine Hilfeoption gibt es laut Manpage nicht. Der Platzhalter `nslookup [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

Optionen auf der Befehlszeile beginnen mit einem Bindestrich und entsprechen den `set`-Schlüsselwörtern des interaktiven Modus:

| Option / `set`-Schlüsselwort | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-type=TYP`, `set type=TYP` | Abfragetyp, etwa `MX`, `NS`, `TXT`, `SOA`. | Abkürzungen `q`, `ty`. Nur ein Typ gleichzeitig. |
| `-timeout=SEKUNDEN` | Erste Wartezeit. | – |
| `-port=PORT`, `set port=PORT` | Anderer Port als 53. | – |
| `set norecurse` | Keine Rekursion anfordern. | Für autoritative Server. |
| `set debug`, `set d2` | Ausführliche Diagnose. | – |
| `set domain=NAME` | Suchliste festlegen. | – |
| `set all` | Aktuelle Einstellungen anzeigen. | Nur interaktiv. |
| `server NAME` | Standardserver wechseln. | Nur interaktiv. |
| `exit` | Interaktiven Modus beenden. | – |
| `-version` | Version anzeigen. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Adresse und Mailserver einer Domain abfragen, einmal direkt und einmal interaktiv. Das sendet DNS-Anfragen; es ist ein **Beispielszenario** und wurde für dieses Dokument nicht ausgeführt.

### Schritt 1: Einfache Abfrage

```bash
nslookup example.org
```

Die Ausgabe nennt zuerst den verwendeten Server, dann Name und Adressen.

### Schritt 2: Mailserver

```bash
nslookup -type=MX example.org
```

### Schritt 3: Interaktiver Modus

```text
$ nslookup
> set type=NS
> example.org
> server 9.9.9.9
> example.org
> exit
```

Damit lassen sich Antworten verschiedener Server schnell vergleichen.

## 6. Typische Anwendungsfälle

- **Plattformübergreifende Anleitungen** (Windows, macOS, Linux) mit gleichem Befehl.
- **Schneller Vergleich** mehrerer DNS-Server im interaktiven Modus.
- **Mailserver und Nameserver** einer Domain ermitteln.
- **Rückwärtsauflösung** einer IP-Adresse.

## 7. Risiken, Nebenwirkungen und Vorsicht

`nslookup` ist rein abfragend. Die ursprüngliche Einstufung „Grün – sicher lesend“ wird als `safe` übernommen. Hinweise:

- **Datenschutz:** Abgefragte Namen sind für den Server sichtbar; ein angegebener fremder Server umgeht unter Umständen einen geschützten Resolver.
- **Nur DNS:** Einträge aus `/etc/hosts` erscheinen nicht.
- **Rückgabewert:** Laut Manpage `1`, wenn irgendeine Abfrage fehlschlug, sonst `0`. Für Skripte mit genauer Auswertung ist `dig` besser geeignet.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `*** Invalid option: -help` | `--help` gibt es nicht (im Test beobachtet). | Manpage lesen; `-version` für die Version. |
| `** server can't find NAME: NXDOMAIN` | Name existiert nicht. | Schreibweise prüfen. |
| `;; connection timed out; no servers could be reached` | Kein Server erreichbar. | Netz und `/etc/resolv.conf` prüfen. |
| `help` im interaktiven Modus ohne Wirkung | Laut Manpage nicht implementiert. | Manpage verwenden. |

**Prüfpunkt:** Außer der ersten Zeile wurden die Meldungen nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Für einfache Prüfungen `host`,** für Details `dig`.
2. **Im interaktiven Modus mit `exit` beenden.**
3. **Für die Systemsicht `getent hosts NAME`.**

### Prüfstand

- **Geprüfte Version:** nslookup 9.18.39 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie.
- **Tatsächlich ausgeführt:** `nslookup -version` und `nslookup --help` (Meldung `*** Invalid option: -help`). Es wurden bewusst **keine DNS-Abfragen** gesendet.
- **Nicht geprüft:** alle Abfragen, Ausgabeformat, interaktive Sitzung, Rückgabewerte bei Fehlern.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `dig` | Ausführliche DNS-Abfragen, gut für Skripte. |
| `host` | Knappe Ausgabe für schnelle Prüfungen. |
| `getent hosts` | Auflösung wie das System sie durchführt. |
| `resolvectl query` | Abfrage über systemd-resolved. |

Ausgangseintrag: Datensatz 162 in `index.json` (`nslookup`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Das Beispiel `nslookup --help` funktioniert nicht und wurde ersetzt. Ergänzt wurden die beiden Betriebsarten, Optionen, nicht implementierte Befehle und Rückgabewerte.
