---
id: "whois"
name: "whois"
command: "whois"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dns", "internet", "domain", "ip-adressen", "registrierung"]
status: "Ausgearbeitet; Quellen geprüft; nur Version praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 176
reviewed_at: "2026-11-13"
locally_checked_version: "whois 5.5.22 (Paket whois 5.5.22)"
---

# whois – Registrierungsdaten von Domains, IP-Adressen und AS-Nummern abfragen

## 1. Kurzbeschreibung

`whois` fragt **Registrierungsdatenbanken** nach dem Protokoll aus RFC 3912 ab. Damit erfährst du zum Beispiel, bei welchem Registrar eine Domain registriert ist, wann sie angelegt wurde und welche Nameserver eingetragen sind, oder welchem Netzbetreiber ein IP-Adressbereich gehört und wo Missbrauch gemeldet werden kann.

**Root-Rechte sind nicht nötig.** `whois` sendet nur Anfragen (TCP-Port 43) und gibt die Antwort aus.

Grundlage ist die [Debian-Manpage zu whois](https://manpages.debian.org/trixie/whois/whois.1.en.html) des Debian-eigenen whois-Clients.

## 2. Was macht der Befehl?

Laut Manpage versucht dieser Client, **den zuständigen Server selbst zu erraten** – etwa anhand der Top-Level-Domain oder des Adressbereichs. Gelingt das nicht, fragt er `whois.networksolutions.com` (für NIC-Handles) oder `whois.arin.net` (für IPv4-Adressen). Bei manchen Registrys folgt er Verweisen von der Registry zum Registrar.

Die Antwort ist **freier Text** im Format des jeweiligen Servers; es gibt kein einheitliches Ausgabeformat. Viele Registrys schwärzen heute personenbezogene Daten. Existiert `/etc/whois.conf`, wird sie laut Manpage zuerst zur Serverwahl herangezogen; auf dem geprüften System gibt es diese Datei nicht.

## 3. Syntax

```text
whois [OPTIONEN] OBJEKT
whois -h SERVER [OPTIONEN] [--] ANFRAGE
```

```bash
whois example.org
whois 192.0.2.10
whois -h whois.ripe.net -b 192.0.2.10
whois AS64496
```

Das bisherige NetMon-Beispiel `whois --help` ist gültig; die Manpage nennt `--help` für die Hilfe. Der Platzhalter `whois [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-h SERVER`, `--host` | Bestimmten whois-Server fragen. | Etwa `whois.ripe.net`. |
| `-p PORT` | Anderer Port. | Vorgabe 43. |
| `-H` | Rechtliche Hinweistexte der Registrys ausblenden. | Kürzere Ausgabe. |
| `-I` | Erst `whois.iana.org` fragen und dem Verweis folgen. | Laut Manpage erhält IANA dann die vollständige Anfrage. |
| `--no-recursion` | Keine Weiterleitung von Registry zu Registrar. | – |
| `--verbose` | Ausführliche Ausgabe, etwa gewählter Server. | Hilft beim Verständnis der Serverwahl. |
| `-b` | Nur Adressbereich mit Missbrauchskontakt (RIPE-artige Server). | Für Missbrauchsmeldungen. |
| `-r` | Keine rekursive Abfrage von Kontaktdaten (RIPE). | – |
| `-T TYP` | Suche auf Objekttypen beschränken (RIPE). | – |
| `--` | Ende der Client-Optionen; Rest geht roh an den Server. | Für serverspezifische Anfragen. |

Laut Manpage werden RIPE-spezifische Optionen bei anderen Servern ignoriert.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Den Missbrauchskontakt für eine IP-Adresse aus einem Protokoll ermitteln. Das sendet Anfragen an whois-Server; es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: Allgemeine Abfrage

```bash
whois 192.0.2.10
```

Die Ausgabe nennt Netzbereich, Betreiber und meist Felder wie `abuse-mailbox` oder `OrgAbuseEmail`.

### Schritt 2: Kurzform bei RIPE

```bash
whois -h whois.ripe.net -b 192.0.2.10
```

Zeigt den kleinsten Adressbereich mit Missbrauchskontakt.

### Schritt 3: Domain prüfen

```bash
whois -H example.org
```

Zeigt Registrar, Daten und Nameserver ohne lange Rechtstexte.

## 6. Typische Anwendungsfälle

- **Missbrauch melden:** Zuständigen Kontakt für auffällige IP-Adressen finden.
- **Domainstatus prüfen:** Ablaufdatum, Registrar, Nameserver.
- **Netzzugehörigkeit klären:** Zu welchem Anbieter gehört eine Adresse? Hilfreich bei Verbindungsanalysen.
- **AS-Nummern** nachschlagen.

## 7. Risiken, Nebenwirkungen und Vorsicht

`whois` ist rein abfragend. Die ursprüngliche Einstufung „Grün – sicher lesend“ wird als `safe` übernommen. Hinweise:

- **Abfragen sind sichtbar:** Die befragten Server sehen, welche Domains oder Adressen dich interessieren. Mit `-I` erhält zusätzlich IANA die Anfrage.
- **Abfragelimits:** Viele Registrys begrenzen die Zahl der Anfragen; automatisierte Massenabfragen können zu Sperren führen.
- **Nutzungsbedingungen:** Die Ausgaben enthalten oft Bedingungen, die etwa Werbung mit den Daten verbieten.
- **Ungenaue Daten:** Einträge können veraltet oder geschwärzt sein; für Entscheidungen weitere Quellen heranziehen.
- **Nicht-ASCII-Zeichen:** Laut Manpage verwenden Server unterschiedliche Zeichenkodierungen.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `No whois server is known for this kind of object.` | Client kennt keinen passenden Server. | Mit `-h SERVER` gezielt fragen (Text im lokalen Programm enthalten, nicht ausgelöst). |
| Sehr knappe Antwort bei `.com`-Domains | Registry-Antwort ohne Registrar-Details. | Verweis auf Registrar-Server folgen (Standard). |
| Abfragelimit überschritten | Zu viele Anfragen. | Warten. |
| Verbindung scheitert | Port 43 durch Firewall blockiert. | Netzwerkregeln prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **`-H` für übersichtlichere Ausgaben.**
2. **Für Missbrauchskontakte `-b`** bei RIPE-artigen Servern.
3. **Keine Massenabfragen.**
4. **`--verbose`,** um zu sehen, welcher Server gefragt wurde.

### Prüfstand

- **Geprüfte Version:** whois 5.5.22 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie.
- **Tatsächlich ausgeführt:** `whois --version` und Prüfung, dass `/etc/whois.conf` nicht existiert. Es wurden bewusst **keine whois-Anfragen** gesendet.
- **Nicht geprüft:** alle Abfragen, Serverwahl, Fehlermeldungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `dig`, `host` | DNS-Einträge einer Domain. |
| `nslookup` | Weitere DNS-Abfragen. |
| `curl` | RDAP-Abfragen (Nachfolgeprotokoll von whois, JSON über HTTPS). **Prüfpunkt:** RDAP nicht geprüft. |

Ausgangseintrag: Datensatz 176 in `index.json` (`whois`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Serverwahl, Optionen einschließlich RIPE-Flags, Anwendungsfälle und Hinweise zu Datenschutz und Abfragelimits ersetzt.
