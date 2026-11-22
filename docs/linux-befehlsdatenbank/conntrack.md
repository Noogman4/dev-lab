---
id: "conntrack"
name: "conntrack"
command: "conntrack"
category: "Netzwerk Grundlagen"
language: "de"
root_required: true
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "conntrack"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 424
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# conntrack – Verbindungsverfolgung ist keine Socketliste

## 1. Kurzbeschreibung

conntrack liest und verändert die Netfilter-Verbindungsverfolgung. Auch lesende Abfragen benötigen typischerweise CAP_NET_ADMIN. Ein getrackter Paketfluss muss keinem lokalen Prozess-Socket entsprechen.

## 2. Was macht der Befehl?

Die Standardtabelle conntrack enthält Flusszustände; expect beschreibt erwartete verwandte Verbindungen. Original- und Antwortrichtung besitzen eigene Tupel, insbesondere bei NAT. TCP-Zustände und Timeouts beschreiben den Kernelstand, nicht die erfolgreiche Anmeldung oder Nutzdatenübertragung. NOTRACK-Ausnahmen und der Namensraum begrenzen die Sicht.

Quelle, am 2026-11-13 gelesen: [Netfilter: conntrack-Handbuch](https://manpages.debian.org/trixie/conntrack/conntrack.8.en.html)

## 3. Syntax

```text
conntrack {-L|-G|-E|-C|-S} [TABELLE] [FILTER]
conntrack {-D|-I|-U|-F} [TABELLE] [PARAMETER]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-L` | Tabelle ausgeben; ohne -z lesend. |
| `-G` | Passenden einzelnen Eintrag suchen. |
| `-E` | Fortlaufenden Ereignisstrom beobachten; kein vollständiger Bestandsdump. |
| `-C`, `-S` | Anzahl beziehungsweise Kernelstatistiken. |
| `-p tcp`, `--dport PORT` | Protokoll und Port der Originalrichtung filtern. |
| `-z` | Beim Lesen Zähler auf null setzen: echte Änderung. |
| `-D`, `-F` | Passende Einträge löschen beziehungsweise Tabelle leeren. |
| `-R DATEI` | Einträge laden; keine bloße Dateianzeige. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
conntrack -L -p tcp --dport 443
```

Das Muster würde getrackte TCP-Flüsse mit Original-Zielport 443 anzeigen. Es beweist weder TLS noch eine offene Firewallregel. NAT kann dazu führen, dass Antwortadressen anders aussehen. Es wurde weder ein Dump noch eine Ereignisüberwachung gestartet.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**NAT nachvollziehen:** Original- und Antworttupel vergleichen. **Störungen eingrenzen:** Trackingzustand neben Routing, Firewall und Socketzustand betrachten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Löschen oder Leeren kann bestehende Verbindungen und zustandsabhängige Freigaben beeinträchtigen. -L -z ist trotz Anzeige schreibend. Ereignisse können bei überlaufendem Empfangspuffer fehlen; eine lückenlose Historie darf daraus nicht behauptet werden. Adressen und Ports sind sensible Betriebsdaten.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Keine Einträge | Filter, Namensraum und Tracking-Ausnahmen prüfen. |
| ENOBUFS | Ereignispuffer überlaufen; Vollständigkeit der Beobachtung offen. |
| Zustand ESTABLISHED | Kein Beleg einer erfolgreichen Anwendungssitzung. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ss` | Lokale Sockets statt Forwarding-Flüsse. |
| `nft` | Regeln können Connection Tracking nutzen. |
| `conntrackd` | Eigenständiger Dienst, nicht dieser CLI-Aufruf. |

Ausgangsdatensatz 424 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
