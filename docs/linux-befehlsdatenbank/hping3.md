---
id: "hping3"
name: "hping3"
command: "hping3"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: true
risk_level: "danger"
tags: ["NetMon Spezial / Diagnoseideen", "hping3"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 406
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; hping3 fehlt"
---

# hping3 – Gezielte Protokollpakete von einem normalen Ping unterscheiden

## 1. Kurzbeschreibung

hping3 erzeugt anpassbare TCP/IP-Pakete und zeigt Antworten an. Der gewöhnliche Aufruf sendet tatsächlich; er ist keine passive Firewallprüfung. Rohe Pakete benötigen üblicherweise Root oder geeignete Capabilities.

## 2. Was macht der Befehl?

Ohne ausdrücklich gewählten Protokollmodus verwendet hping3 TCP, nicht ICMP. Flags, Zielport und zeitlicher Abstand bestimmen den Versuch. Eine TCP-SYN-Antwort, ein Reset und fehlende Antwort sind verschiedene Beobachtungen; keine davon beweist allein die Ursache einer Filterung. Das alte Handbuch enthält historische Aussagen und einzelne widersprüchliche Ratenbeschreibungen. Für begrenzte Versuche zählen deshalb konkrete Intervallangabe und lokale Hilfe, nicht Werbeaussagen über Geschwindigkeit.

Quelle, am 2026-11-13 gelesen: [hping-Projekthandbuch](https://manpages.debian.org/trixie/hping3/hping3.8.en.html)

## 3. Syntax

```text
hping3 [MODUS] [OPTIONEN] ZIEL
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-1` / `--icmp` | ICMP-Modus statt Standard-TCP wählen. |
| `-2` / `--udp` | UDP-Pakete senden. |
| `-S` | TCP-SYN-Flag setzen; kein vollständiger Anwendungstest. |
| `-p PORT` | Zielport wählen, kein Serverstart. |
| `-c ANZAHL` | Sendung begrenzen; Antworten können danach noch abgewartet werden. |
| `-i SEKUNDEN` | Sendeabstand; Mikrosekundenform unterscheidet sich deutlich. |
| `-n` | Namensauflösung für Anzeigen vermeiden. |
| `--flood`, `--rand-source` | Hochlast-/gefälschte Quellenmodi; für diesen Auftrag ausgeschlossen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
hping3 -1 -n -c 3 -i 1 ZIEL
```

Das nicht ausgeführte Muster würde maximal drei ICMP-Versuche mit einer Sekunde Abstand an ein vorher autorisiertes Ziel senden. Laufzeit und Verlustquote sind hier nicht gemessen. Ein Timeout könnte an Hinweg, Rückweg, Antwortpolitik oder Paketverlust liegen; es rechtfertigt keine Laststeigerung.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Protokolldiagnose planen: Pakettyp, Ziel, Anzahl und Abstand vorab festlegen. Antworten verstehen: Transportreaktion von Anwendungsverfügbarkeit trennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Paketgeneratoren verändern den Netzwerkverkehr und können Überwachung, Sperren oder Last auslösen. Kein Spoofing, keine Zufallsziele, Scans oder Flutmodi als Übung. Keine Capabilities oder Firewallregeln ändern. Nur eigene oder gesondert autorisierte Ziele kämen für spätere Tests infrage.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Operation not permitted | Rohpaketrechte fehlen; hier nicht eskalieren. |
| Keine Antwort | Keine eindeutige Aussage über Firewall oder Hostzustand. |
| TCP statt ICMP | Standardmodus und ausgewählte Flags prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; hping3 fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ping` | Spezialisierter ICMP-Echotest. |
| `nping` | Anderer Paketgenerator. |
| `tcpdump` | Mitschnitt statt eigener Probe. |

Ausgangsdatensatz 406 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
