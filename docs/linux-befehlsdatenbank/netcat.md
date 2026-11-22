---
id: "netcat"
name: "netcat"
command: "netcat"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "tcp", "udp", "sockets"]
status: "Ausgearbeitet; Quellen geprüft; nur Alternativen-Zuordnung und Hilfe praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 161
reviewed_at: "2026-11-13"
locally_checked_version: "netcat → OpenBSD netcat 1.226 (Paket netcat-openbsd 1.226-1ubuntu2)"
---

# netcat – Langname für nc und seine verschiedenen Implementierungen

## 1. Kurzbeschreibung

`netcat` ist der ausgeschriebene Name des Netzwerkwerkzeugs, das meist als `nc` aufgerufen wird. Es öffnet TCP- oder UDP-Verbindungen, lauscht auf Ports und leitet Daten zwischen Standardein- und -ausgabe und dem Netz weiter.

**Wichtig:** Hinter dem Namen `netcat` steckt je nach System ein **anderes Programm**. Auf dem geprüften System ist `/usr/bin/netcat` über das Alternativen-System ein Nebenlink der Gruppe `nc` und zeigt auf **OpenBSD netcat** (`/bin/nc.openbsd`). Die Bedienung entspricht deshalb genau dem Dokument zu `nc`.

**Root-Rechte sind meist nicht nötig;** Ausnahmen sind Ports unter 1024.

## 2. Was macht der Befehl?

Die Grundfunktion beschreibt die [Debian-Manpage zur traditionellen Fassung](https://manpages.debian.org/trixie/netcat-traditional/nc.traditional.1.en.html) so: `nc host port` baut eine TCP-Verbindung auf, sendet die Standardeingabe und gibt alles aus, was zurückkommt – bis die Gegenseite die Verbindung beendet.

Unter Debian und Ubuntu gibt es drei Pakete, die den Namen belegen können:

| Paket | Programm | Besonderheit |
| --- | --- | --- |
| `netcat-openbsd` | `nc.openbsd` | Unix-Sockets, Proxys, kein `-e`; auf dem Prüfsystem aktiv. |
| `netcat-traditional` | `nc.traditional` | Ältere Fassung mit `-e` und `-c` zum Ausführen von Programmen. |
| `ncat` (Nmap) | `ncat` | TLS, Zugriffslisten, Broker; die Debian-Manpage `netcat(1)` in trixie gehört zu diesem Paket. |

Welche Fassung aktiv ist, zeigt:

```bash
readlink -f "$(command -v netcat)"
update-alternatives --display nc
```

## 3. Syntax

Für die auf dem Prüfsystem aktive OpenBSD-Fassung:

```text
netcat [OPTIONEN] [ZIEL] [PORT]
netcat -l [OPTIONEN] [ADRESSE] PORT
netcat -U [-l] SOCKETPFAD
```

```bash
netcat -zv example.org 443
netcat -h
```

Das bisherige NetMon-Beispiel `netcat --help` ist bei OpenBSD netcat keine gültige Option (Meldung `invalid option -- '-'` mit anschließender Kurzhilfe); vorgesehen ist `-h`. Der Platzhalter `netcat [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

Für OpenBSD netcat gelten die Optionen aus dem Dokument zu `nc` (Quelle: [Debian-Manpage nc.openbsd](https://manpages.debian.org/trixie/netcat-openbsd/nc.openbsd.1.en.html)). Die wichtigsten:

| Option | Bedeutung |
| --- | --- |
| `-l` | Lauschen statt verbinden. |
| `-z` | Nur prüfen, ob ein Dienst lauscht. |
| `-v` | Ausführliche Meldungen. |
| `-w SEKUNDEN` | Zeitlimit. |
| `-u` | UDP. |
| `-U` | Unix-Domain-Socket. |
| `-N` | Socket nach Eingabeende schließen. |
| `-h` | Hilfe. |

Unterschiede zur traditionellen Fassung: Dort gibt es `-e PROGRAMM` und `-c BEFEHLE`, die nach dem Verbindungsaufbau ein Programm beziehungsweise Shell-Befehle ausführen – laut Manpage „use with caution“.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Feststellen, welche netcat-Fassung installiert ist, bevor man Anleitungen aus dem Internet folgt.

### Schritt 1: Ziel des Befehls ermitteln

```bash
readlink -f "$(command -v netcat)"
```

Auf dem geprüften System: `/usr/bin/nc.openbsd`.

### Schritt 2: Alternativen ansehen

```bash
update-alternatives --display nc
```

Zeigt die Gruppe `nc` mit dem Nebenlink `netcat` und die verfügbaren Fassungen. Auf dem Prüfsystem war nur `/bin/nc.openbsd` eingetragen.

### Schritt 3: Hilfe der aktiven Fassung

```bash
netcat -h
```

Die erste Zeile nennt die Fassung, hier `OpenBSD netcat (Debian patchlevel 1.226-1ubuntu2)`.

### Schritt 4: Anleitung prüfen

Verwendet eine Anleitung `-e` oder `-c`, ist sie für die traditionelle Fassung oder `ncat` geschrieben und funktioniert mit OpenBSD netcat nicht.

## 6. Typische Anwendungsfälle

Siehe `nc`: Ports prüfen, Protokolle von Hand testen, Daten im lokalen Netz übertragen, lokale Sockets ansprechen, SSH-Proxyverbindungen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nicht zu. Der Kopf verwendet `caution`:

- **Unterschiedliche Fassungen:** Ein Skript kann auf einem anderen System ein Programm mit ganz anderen Optionen aufrufen.
- **Programmausführung:** Mit der traditionellen Fassung oder `ncat` kann `-e`/`-c` eine Shell an einen Port binden.
- **Offene Ports und Klartext** wie bei `nc`.
- **Portscans** fremder Systeme nur mit Erlaubnis.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `invalid option -- '-'` bei `--help` | OpenBSD-Fassung ohne lange Optionen. | `netcat -h`. |
| Option `-e` unbekannt | OpenBSD-Fassung. | Bewusst so; Anleitung prüfen. |
| `netcat: command not found` | Kein netcat-Paket installiert. | `nc` probieren oder Paket wählen. |
| Verhalten weicht von Anleitung ab | Andere Implementierung. | Fassung mit `readlink -f` ermitteln. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Fassung immer zuerst prüfen.**
2. **In Skripten die gewünschte Fassung direkt aufrufen** (`nc.openbsd`, `ncat`).
3. **Mit Unix-Sockets oder `127.0.0.1` üben** (Ablauf im Dokument zu `nc`).
4. **Kein `-e`/`-c` an erreichbaren Ports.**

### Prüfstand

- **Geprüfte Version:** OpenBSD netcat 1.226 über `/usr/bin/netcat`.
- **Tatsächlich ausgeführt:** Auflösung der Verweise (`readlink -f`), `update-alternatives --display nc` (nur Lesen), `netcat -h` beziehungsweise `nc -h` und `nc --help`. Der Unix-Socket-Ablauf ist im Dokument zu `nc` beschrieben und geprüft.
- **Nicht geprüft:** traditionelle Fassung und `ncat` (nicht installiert), Netzwerkverbindungen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `nc` | Kurzname; ausführliches Dokument mit geprüftem Ablauf. |
| `ncat` | Nmap-Variante mit TLS und Zugriffslisten. |
| `socat` | Universelles Werkzeug für Datenkanäle. |
| `update-alternatives` | Zeigt und wählt die aktive Fassung. |

Ausgangseintrag: Datensatz 161 in `index.json` (`netcat`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch die Zuordnung des Namens zu verschiedenen Implementierungen, den Prüfweg zur aktiven Fassung und die Risiken der Programmausführung ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
