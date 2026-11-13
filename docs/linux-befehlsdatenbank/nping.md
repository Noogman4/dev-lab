---
id: "nping"
name: "nping"
command: "nping"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["NetMon Spezial / Diagnoseideen", "nping"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 413
reviewed_at: "2026-11-13"
locally_checked_version: "Nping 0.7.94SVN"
---

# nping – Nping-Proben gezielt planen

## 1. Kurzbeschreibung

nping erzeugt Netzwerkproben und analysiert Antworten. TCP-Connect kann ohne besondere Rechte laufen; Raw-TCP, ICMP oder ARP haben andere Rechteanforderungen. Jeder echte Zielaufruf kann Verkehr erzeugen.

## 2. Was macht der Befehl?

Der Probenmodus ist ausdrücklich von der Zielangabe zu trennen. TCP-Connect benutzt den Betriebssystemstack, rohe Modi erlauben Headersteuerung. -c zählt Runden: Mehrere Ziele und Ports vervielfachen die Paket-/Verbindungszahl. Der Nping-Echo-Modus benötigt eine eigene Gegenstelle und untersucht Veränderungen im Transit; er ist nicht identisch mit ICMP Echo. Eine erfolglose Antwortanalyse beweist keine eindeutige Firewallursache.

Quelle, am 2026-11-13 gelesen: [Nmap-Projekt: Nping-Handbuch](https://nmap.org/book/nping-man.html) und lokale Hilfe

## 3. Syntax

```text
nping PROBENMODUS [OPTIONEN] ZIEL...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--tcp-connect` | Unprivilegierte Verbindungsprobe. |
| `--tcp`, `--icmp`, `--udp` | Andere aktive Probenmodi. |
| `-p PORTLISTE` | Transportziele auswählen; jeder Port kann eigene Versuche erzeugen. |
| `-c RUNDEN` | Rundenzahl begrenzen, nicht pauschal Gesamtpaketanzahl. |
| `--delay ZEIT` | Abstand zwischen Proben, Einheiten ausdrücklich wählen. |
| `-N` | Antwortcapture abschalten; unterbindet nicht das Senden. |
| `--privileged` | Nimmt Rechte an, erteilt sie aber nicht. |
| `-V` | Version ausgeben ohne Probenziel. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
nping --tcp-connect -p 443 -c 1 --delay 1s ZIEL
```

Das Muster beschreibt eine begrenzte Verbindungsprobe zu genau einem vorher autorisierten Ziel und Port. Es wird kein TLS-Handshake oder Zertifikatsnachweis versprochen. Keine Verbindung wurde aufgebaut. -N wäre kein Trockenlauf und würde die Sendewirkung nicht beseitigen.

### Schritt 3: Aussagegrenze festhalten

Ein Hilfe-/Versionsaufruf wird unten gesondert belegt. Er bestätigt nur die lokale Schnittstelle, nicht den Ablauf des Musters.

## 6. Typische Anwendungsfälle

Probenumfang verstehen: Ziele mal Ports mal Runden zählen. Transportfehler eingrenzen: Connect und Rawmodus mit ihren unterschiedlichen Voraussetzungen vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Proben erreichen andere Teilnehmer und können Logs, Sperren und Last auslösen. Kein Spoofing, kein ARP-Eingriff, kein Echostart und keine breite Zielmenge als Beispieltest. Rechteannahmen ersetzen keine tatsächlichen Capabilities.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Raw mode not permitted | Modusrechte prüfen; keine Privilegänderung durchführen. |
| Mehr Pakete als count | Count sind Runden über die gewählte Menge. |
| Connect erfolgreich | Nur Transportaufbau belegt, keine sichere Anwendung. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nping 0.7.94SVN. Praktisch geprüft: Nur Hilfe/Version ausgeführt; Beispiel, echte Netz-/Geräte-/Sitzungszugriffe und zustandsändernde Modi nicht praktisch geprüft. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `hping3` | Anderer Paketgenerator. |
| `ping` | ICMP-Echo. |
| `ss` | Lokale Socketansicht. |

Ausgangsdatensatz 413 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
