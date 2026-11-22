---
id: "mosh"
name: "mosh"
command: "mosh"
category: "Cloud & Remote"
language: "de"
root_required: false
risk_level: "caution"
tags: ["cloud", "remote", "terminal", "ssh"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 132
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# mosh – Robuste Terminalverbindung für wechselnde Netze

## 1. Kurzbeschreibung

`mosh` („mobile shell“) ist ein Terminal-Fernzugang wie `ssh`, der auch bei **instabilen oder wechselnden Verbindungen** bestehen bleibt: nach dem Ruhezustand des Laptops, beim Wechsel zwischen WLAN und Mobilfunk oder bei Paketverlust. Tastatureingaben werden auf langsamen Verbindungen sofort lokal angezeigt.

**Root-Rechte sind nicht nötig** – weder auf dem eigenen Rechner noch auf dem Server. Auf dem Server muss jedoch das Programm `mosh-server` vorhanden sein (es kann laut Manpage auch im Heimatverzeichnis liegen), und eine Firewall muss UDP-Pakete durchlassen. Das Freigeben von Ports in einer Server-Firewall ist eine Verwaltungsaufgabe.

Grundlage ist die [Debian-Manpage zu mosh](https://manpages.debian.org/trixie/mosh/mosh.1.en.html). Auf dem geprüften System ist `mosh` nicht installiert.

## 2. Was macht der Befehl?

Der Ablauf laut Manpage:

1. `mosh` baut zunächst eine normale **SSH-Verbindung** auf und meldet sich mit den üblichen SSH-Verfahren an (Schlüssel oder Passwort).
2. Über SSH startet es auf dem Server das unprivilegierte Hilfsprogramm `mosh-server`.
3. Danach wird die SSH-Verbindung geschlossen. Der lokale `mosh-client` hält eine eigene, langlebige Verbindung über **UDP**, standardmäßig auf einem Port zwischen **60000 und 61000**.

Die Verbindung übersteht Wechsel der IP-Adresse des Clients. Eine **Vorhersage** zeigt Eingaben auf langsamen Leitungen sofort an und unterstreicht sie, bis der Server sie bestätigt. Passwörter und nicht angezeigte Eingaben werden dabei laut Manpage nicht vorab angezeigt.

### Was mosh nicht kann

Laut Manpage unterstützt `mosh` **keine X-Weiterleitung, keine Portweiterleitung, kein sshfs** und keine anderen nicht interaktiven SSH-Funktionen. Die IPv6-Unterstützung ist eingeschränkt; pro Sitzung wird eine Serveradresse festgelegt. Ein Rollen durch ältere Ausgaben („Scrollback“) bietet `mosh` nur eingeschränkt; dafür wird es oft mit `tmux` oder `screen` kombiniert. **Prüfpunkt:** Die Aussage zum Scrollback stammt nicht aus der gelesenen Manpage.

## 3. Syntax

```text
mosh [OPTIONEN] [BENUTZER@]HOST [BEFEHL ...]
```

```bash
mosh anna@server.example.org
mosh --ssh="ssh -p 2222" anna@server.example.org
mosh -p 60001 anna@server.example.org -- tmux attach
```

Das bisherige NetMon-Beispiel `mosh --help` zeigt nur die Hilfe; der Platzhalter `mosh [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--ssh=BEFEHL` | SSH-Aufruf anpassen. | Etwa `--ssh="ssh -p 2222"` für einen anderen SSH-Port. |
| `-p PORT[:PORT2]`, `--port=...` | Bestimmten UDP-Port oder Bereich verwenden. | Wenn in der Firewall nur dieser Port offen ist; betrifft nicht den SSH-Port. |
| `--predict=adaptive/always/never` | Lokale Vorhersage steuern. | `-a` = immer, `-n` = nie. |
| `-o`, `--predict-overwrite` | Vorhersage überschreibt statt einzufügen. | – |
| `-4`, `-6`, `--family=...` | Adressfamilie wählen. | Standard: `prefer-inet`. |
| `--server=BEFEHL` | Pfad zum `mosh-server` auf dem Server. | Bei Installation im Heimatverzeichnis. |
| `--bind-server=ssh/any/IP` | Bindung des Servers festlegen. | Für Server mit mehreren Adressen. |
| `--no-init` | Alternativen Bildschirm nicht verwenden. | – |
| `--local` | `mosh-server` lokal ohne SSH starten. | Nur zum Testen mit numerischer lokaler Adresse. |

### Escape-Sequenz

Das Escape-Zeichen ist standardmäßig `Strg+^` (auf US-Tastaturen `Strg+Umschalt+6`). `Esc` gefolgt von `.` beendet die Verbindung, `Esc` gefolgt von `Strg+Z` hält den Client an. Auf deutschen Tastaturen kann das Zeichen schwer erreichbar sein; die Manpage verweist auf die Variable `MOSH_ESCAPE_KEY`.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Eine dauerhafte Terminalsitzung zu einem eigenen Server aufbauen. Voraussetzungen: SSH-Zugang funktioniert, `mosh` ist auf beiden Seiten installiert, UDP-Ports sind freigegeben. Es ist ein **Beispielszenario** und wurde nicht ausgeführt.

### Schritt 1: SSH vorab prüfen

```bash
ssh anna@server.example.org true
```

Funktioniert das nicht, kann auch `mosh` keine Verbindung aufbauen.

### Schritt 2: Verbindung aufbauen

```bash
mosh anna@server.example.org
```

Nach der SSH-Anmeldung erscheint die normale Shell des Servers.

### Schritt 3: Netzwechsel ausprobieren

Laptop kurz in den Ruhezustand versetzen oder WLAN wechseln. Oben im Fenster erscheint ein Hinweis auf die Unterbrechung; nach Rückkehr des Netzes läuft die Sitzung weiter.

### Schritt 4: Beenden

In der Shell `exit` eingeben. Bei hängender Verbindung `Strg+^` und dann `.` drücken.

## 6. Typische Anwendungsfälle

- **Arbeiten unterwegs** über Mobilfunk oder öffentliche WLANs.
- **Hohe Latenz:** Eingaben erscheinen sofort, statt auf den Server zu warten.
- **Lange Sitzungen** zusammen mit `tmux` oder `screen` auf dem Server.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ passt nicht: `mosh` ist ein Fernzugang, über den beliebige Befehle auf dem Server laufen. Der Kopf verwendet `caution`.

- **Offene UDP-Ports:** Der Server braucht freie UDP-Ports (Standard 60000–61000). Ein großer offener Bereich vergrößert die Angriffsfläche; mit `-p` lässt sich ein einzelner Port nutzen.
- **Verwaiste Server-Prozesse:** Bricht der Client ab, kann `mosh-server` auf dem Server weiterlaufen und auf eine Wiederverbindung warten. **Prüfpunkt:** genaues Zeitverhalten nicht geprüft.
- **Gleiche Anmeldesicherheit wie SSH:** Schwache SSH-Anmeldung bleibt schwach.
- **Netzwerküberwachung:** Unbekannter UDP-Verkehr auf hohen Ports kann in Überwachungssystemen auffallen.
- **Vorhersage:** Kann kurzzeitig falsche Zeichen anzeigen, die nach einer Rundreise korrigiert werden.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `mosh-server: command not found` | Server-Programm fehlt. | Auf dem Server installieren oder `--server=PFAD`. |
| Verbindung hängt nach SSH-Anmeldung | UDP blockiert. | Firewall prüfen; festen Port mit `-p`. |
| Fehler zur Zeichensatz-Umgebung | Keine UTF-8-Locale auf einer Seite. | UTF-8-Locale einrichten. |
| Fehler bei Dual-Stack-Hosts | `--family=auto` und beide Adressfamilien. | `-4`, `-6` oder `--family=all`. |
| Escape-Taste nicht erreichbar | Tastaturbelegung. | `MOSH_ESCAPE_KEY` setzen. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Erst `ssh` zum Laufen bringen,** dann `mosh` verwenden.
2. **Einen festen UDP-Port** freigeben statt des ganzen Bereichs.
3. **Mit `tmux` auf dem Server kombinieren,** damit Sitzungen auch nach Abbruch des Clients erhalten bleiben.
4. **SSH-Schlüssel statt Passwörtern** verwenden.

### Prüfstand

- **Geprüfte Version:** keine; `mosh` ist nicht installiert.
- **Quellen gelesen:** Debian-Manpage `mosh(1)` (Ablauf, Optionen, Escape-Sequenzen), Abruf 2026-11-13.
- **Nicht geprüft:** jede Verbindung, Firewall-Verhalten, Fehlermeldungen, Lebensdauer verwaister Server-Prozesse.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ssh` | Grundlage für Anmeldung; bietet Weiterleitungen, die `mosh` nicht hat. |
| `mosh-server`, `mosh-client` | Die beiden Hilfsprogramme von `mosh`. |
| `tmux`, `screen` | Halten Sitzungen auf dem Server dauerhaft. |
| `ufw` | Freigabe der UDP-Ports auf dem Server. |

Ausgangseintrag: Datensatz 132 in `index.json` (`mosh`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch den tatsächlichen Verbindungsablauf über SSH und UDP, Grenzen, Optionen und Netzwerkvoraussetzungen ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
