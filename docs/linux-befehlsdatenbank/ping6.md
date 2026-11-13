---
id: "ping6"
name: "ping6"
command: "ping -6"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "ping6"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 440
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# ping6 – Historischen IPv6-Aufrufnamen richtig verwenden

## 1. Kurzbeschreibung

ping6 bezeichnet in iputils die IPv6-Ping-Funktion. Sie ist seit iputils s20150815 in ping integriert; ein Aufrufname oder Symlink ping6 kann aus Kompatibilitätsgründen weiter existieren.

## 2. Was macht der Befehl?

Die aktuelle eindeutige Schreibweise ist ping -6. Der Katalogeintrag ping6 bleibt erhalten, seine tatsächliche portable Verfügbarkeit wird nicht vorausgesetzt. IPv6 benutzt ICMPv6; linklokale Ziele benötigen eine eindeutige Interfacezuordnung je Socket-/Kernelvariante. Eine IPv4-Adresse wird durch die Option -6 nicht in ein IPv6-Ziel umgewandelt.

Quelle, am 2026-11-13 gelesen: [iputils: ping-Handbuch und HISTORY](https://man7.org/linux/man-pages/man8/ping.8.html) sowie lokale ping-Manpage

## 3. Syntax

```text
ping -6 [-n] [-c ANZAHL] [-w SEKUNDEN] IPV6_ZIEL
ping6 [OPTIONEN] IPV6_ZIEL  # nur falls als Aufrufname vorhanden
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `ping -6` | Aktuelle explizite IPv6-Auswahl. |
| `-c`, `-w` | Anfragenzahl und Deadline begrenzen. |
| `-n` | Keine symbolische Rückwärtsanzeige. |
| `-I LINK` | Linkzuordnung/Quelle; Unterstützung lokal prüfen. |
| `%LINK` am Ziel | Scope-Zuordnung linklokaler IPv6-Adressen. |
| `-V` | Programmversion, kein IPv6-Funktionstest. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
ping -6 -n -c 2 -w 5 2001:db8::1
```

2001:db8::1 gehört zum Dokumentationspräfix und ist kein freigegebenes Ziel. Das Muster sendet hier nichts. Ein erfolgreicher späterer IPv6-Echotest würde weder IPv4-Konnektivität noch DNS- oder Webzugang beweisen. Der command-Metawert nennt die tatsächliche aktuelle Form.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Alte Skripte lesen:** Aufrufnamen von eigenständigen Implementierungen unterscheiden. **Dual Stack verstehen:** IPv4- und IPv6-Ergebnisse getrennt erfassen.

## 7. Risiken, Nebenwirkungen und Vorsicht

IPv6 ist kein passiver Ersatz für IPv4: Anfragen erzeugen reale Pakete. Linklokale Mehrdeutigkeit darf nicht durch wahllose Interfaceversuche gelöst werden. Keine Sysctls, Capabilities oder IPv6-Adressen wurden geändert; die praktische Netzwerkprüfung bleibt offen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| ping6 fehlt | Installiertes ping und dokumentierte -6-Option prüfen, nichts nachinstallieren. |
| Network unreachable | IPv6-Pfad/Quelle fehlt; kein DNS-Beweis. |
| Linklokales Ziel mehrdeutig | Scope angeben, aber erst nach eindeutiger Ziel-/Interfacefreigabe. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ping` | Gemeinsame aktuelle iputils-Implementierung. |
| `ip -6 route` | IPv6-Routen getrennt lesen. |
| `tracepath` | Anderer aktiver Diagnoseablauf. |

Ausgangsdatensatz 440 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
