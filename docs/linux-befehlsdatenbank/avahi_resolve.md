---
id: "avahi_resolve"
name: "avahi-resolve"
command: "avahi-resolve"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["NetMon Spezial / Diagnoseideen", "avahi-resolve"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 403
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# avahi-resolve – mDNS-/DNS-Namen über Avahi auflösen

## 1. Kurzbeschreibung

avahi-resolve übersetzt Namen in Adressen oder Adressen in Namen und verwendet dabei den Avahi-Daemon. Ein normaler Benutzer braucht dafür kein Root, aber Zugriff auf den laufenden Dienst. Der Aufruf kann echte Namensanfragen erzeugen.

## 2. Was macht der Befehl?

Der Modus muss ausdrücklich gewählt werden: -n für vorwärts und -a für rückwärts. Ein vollständig angegebener Name ist von einer DNS-SD-Dienstinstanz zu unterscheiden. Die Antwort beschreibt eine Namenszuordnung zum Abfragezeitpunkt. Sie prüft weder einen TCP-Port noch die Echtheit des Hosts. Rückwärts- und Vorwärtsauflösung müssen nicht symmetrisch sein; verschiedene Resolverwege können andere Ergebnisse liefern.

Quelle, am 2026-11-13 gelesen: [Avahi-Projekthandbuch: avahi-resolve](https://manpages.debian.org/trixie/avahi-utils/avahi-resolve.1.en.html)

## 3. Syntax

```text
avahi-resolve --name [OPTIONEN] NAME...
avahi-resolve --address [OPTIONEN] ADRESSE...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-n` / `--name` | Vollständige Hostnamen in Adressen übersetzen. |
| `-a` / `--address` | Adressen rückwärts in Namen auflösen. |
| `-4`, `-6` | Bei Namensauflösung IPv4 beziehungsweise IPv6 anfordern. |
| `-v` | Ausführlichere Meldungen. |
| `-V`, `-h` | Version beziehungsweise Hilfe ohne Zielaufruf. |
| `avahi-resolve-host-name` | Alternativer Aufrufname mit vorausgewähltem Namensmodus. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
avahi-resolve -n -4 lernrechner.local
```

Der erfundene Name würde über Avahi nach einer IPv4-Adresse aufgelöst. Eine erfolgreiche Namens-/Adresszeile wäre kein Ping und kein Beweis für einen verfügbaren Anwendungsdienst. Hier wurde der Name nicht angefragt. Für eine spätere echte Prüfung wären Netzsegment und Zeitpunkt mit festzuhalten.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Namensprobleme eingrenzen: Avahi-Antwort von NSS- und klassischen DNS-Wegen unterscheiden. Adressfamilie prüfen: IPv4-/IPv6-Auswahl gezielt verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

mDNS-Antworten sind nicht automatisch authentisiert. Abfragen geben Namen ins Netz preis. Ergebnisse nicht ungeprüft in Befehle oder Vertrauenslisten übernehmen. Keine Avahi-, NSS-, DNS- oder Firewalländerungen für den Beispielnachweis.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Timeout | Keine passende Antwort oder Dienst-/Netzzugriff eingeschränkt. |
| Anderes Ergebnis als getent | Andere Auflösungspfade und Caches vergleichen. |
| Dienstinstanz statt Hostname | DNS-SD-Browsing und Hostauflösung unterscheiden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `avahi-browse` | Dienstinstanzen entdecken. |
| `getent hosts` | NSS-Sicht. |
| `resolvectl` | Resolververwaltung/-abfragen mit eigener Semantik. |

Ausgangsdatensatz 403 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
