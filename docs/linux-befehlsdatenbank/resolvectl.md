---
id: "resolvectl"
name: "resolvectl"
command: "resolvectl"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "resolvectl"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 441
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# resolvectl – Resolverzustand von aktiver Anfrage unterscheiden

## 1. Kurzbeschreibung

resolvectl arbeitet mit systemd-resolved. status zeigt dessen globale und linkbezogene Einstellungen; query löst Namen oder Adressen auf und kann Netzverkehr auslösen.

## 2. Was macht der Befehl?

Der Resolver kann klassische DNS-Abfragen, lokale Quellen und abhängig von Konfiguration weitere Protokolle verwenden. Eine als authenticated markierte Antwort muss nicht aus einer DNSSEC-validierten öffentlichen Zone stammen: Auch lokal vertrauenswürdige Quellen können so gekennzeichnet sein. Resolverkonfiguration, tatsächlich verwendeter Link und Anwendungssicht sind getrennte Fragen.

Quelle, am 2026-11-13 gelesen: [systemd: resolvectl-Handbuch](https://www.freedesktop.org/software/systemd/man/latest/resolvectl.html)

## 3. Syntax

```text
resolvectl [OPTIONEN] {status|query|statistics} [ARGUMENTE]
resolvectl dns LINK [SERVER...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `status [LINK]` | Wirksame globale/Link-Einstellungen anzeigen. |
| `query NAME` | Aktive Namens-/Adressauflösung. |
| `--type=TYP` | Konkreten Resource-Record-Typ abfragen. |
| `statistics` | Resolverstatistik lesen. |
| `flush-caches` | Dienstcache leeren; echte Zustandsänderung. |
| `dns`, `domain` mit Werten | Link-DNS-/Such- oder Routingdomains ändern. |
| `revert LINK` | Linkkonfiguration zurücksetzen, kein Lesemodus. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
resolvectl status eth-lernen
```

Das Muster würde nur den erfundenen Linkstatus anfordern. Es misst keine erfolgreiche DNS-Antwort. Ein aufgelisteter DNS-Server kann konfiguriert und dennoch unerreichbar sein. Ein Präfix ~ bei einer Domain bezeichnet eine Routingdomain und nicht automatisch eine normale Suchdomain.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**DNS-Zuständigkeit verstehen:** Dienststatus neben Netzwerkmanager und Anwendung betrachten. **Split DNS planen:** Linkzuordnung und Routingdomains ausdrücklich dokumentieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

query kann Namen an konfigurierte Resolver übermitteln. DNS-/Domain-Änderungen können Auflösung umleiten und werden möglicherweise von einem Manager überschrieben. Cacheleeren ist kein allgemeiner Reparaturbeweis. Keine Dienste abgefragt, Caches geleert oder Resolverwerte geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Dienst nicht erreichbar | systemd-resolved ist Voraussetzung; nicht automatisch starten. |
| Server angezeigt, Anfrage scheitert | Konfiguration und Erreichbarkeit unterscheiden. |
| Authenticated falsch gedeutet | Lokale Vertrauensquelle versus DNSSEC unterscheiden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `systemd-resolve` | Historische Oberfläche mit anderer Syntax. |
| `nmcli` | Kann linkbezogene DNS-Daten bereitstellen. |
| `dig` | Direkte DNS-Abfragen mit eigener Resolverwahl. |

Ausgangsdatensatz 441 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
