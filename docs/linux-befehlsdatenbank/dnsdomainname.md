---
id: "dnsdomainname"
name: "dnsdomainname"
command: "dnsdomainname"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "safe"
tags: ["Netzwerk Grundlagen", "dnsdomainname"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 425
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# dnsdomainname – DNS-Domänenteil des aufgelösten Hostnamens anzeigen

## 1. Kurzbeschreibung

dnsdomainname aus net-tools zeigt den Domänenteil des kanonisch aufgelösten lokalen Hostnamens. Es setzt keine DNS-Domain und ist kein allgemeines DNS-Abfragewerkzeug.

## 2. Was macht der Befehl?

Der Systemhostname und das vom Resolver gelieferte FQDN können voneinander abweichen. NSS und lokale Hosts-Einträge beeinflussen das Ergebnis; je nach Konfiguration kann auch Netzauflösung stattfinden. Für den erfundenen FQDN lernpc.beispiel.invalid wäre beispiel.invalid der Domänenteil. Das sagt nichts über Suchdomains, DNS-Server oder NIS aus.

Quelle, am 2026-11-13 gelesen: [net-tools: hostname/dnsdomainname-Handbuch](https://man7.org/linux/man-pages/man1/hostname.1.html)

## 3. Syntax

```text
dnsdomainname [-v]
dnsdomainname --help
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| Ohne Argument | Domänenteil des aufgelösten FQDN anzeigen. |
| `-v` | Zusätzliche Diagnose; kein Setzmodus. |
| `--help` | Hilfe der installierten Variante. |
| `hostname --fqdn` | Verwandter Aufruf zeigt den vollständigen kanonischen Namen. |
| `hostname --domain` | Entsprechende Anzeige über hostname. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
Erfundener FQDN: lernpc.beispiel.invalid
Gedachter Domänenteil: beispiel.invalid
Nicht ausgeführter Aufruf: dnsdomainname
```

Das Zerlegen des erfundenen Namens erklärt das erwartete Feld. Es ist keine gemessene Resolverantwort. Ein leerer Domänenteil ist möglich, wenn der kanonische Name keinen Punkt enthält. Ein Auflösungsfehler muss von einer leeren Domain unterschieden werden.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Namensverständnis:** Hostname, FQDN und Domain unterscheiden. **Diagnose planen:** Resolverkonfiguration neben dem angezeigten Wert betrachten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der Aufruf kann konfigurierte Resolver und dadurch Netzwerkdienste nutzen. Er korrigiert keine DNS-Zone und registriert keinen Namen. Systemdateien werden für diese Dokumentation nicht geändert. Ein fremder String als zusätzliches Argument ist kein zulässiger Domain-Setzauftrag.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Name or service not known | Lokaler Hostname lässt sich nicht kanonisch auflösen. |
| Domain unerwartet | NSS-/Hosts-Ergebnis und FQDN getrennt prüfen. |
| NIS-Wert erwartet | domainname/nisdomainname sind andere Anzeigen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `hostname` | Systemhostname und FQDN anzeigen. |
| `domainname` | NIS-Domain, nicht DNS-Domain. |
| `resolvectl` | Resolverstatus und konkrete DNS-Anfragen. |

Ausgangsdatensatz 425 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
