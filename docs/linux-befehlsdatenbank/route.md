---
id: "route"
name: "route"
command: "route"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "route"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 442
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# route – Legacy-Routenanzeige ohne Konfigurationsauftrag

## 1. Kurzbeschreibung

route aus net-tools zeigt ohne add/del die Kernelrouten. Mit add oder del verändert es Routing. Moderne Policy-Routing-Fragen werden mit ip route und ip rule genauer abgebildet.

## 2. Was macht der Befehl?

Zielnetz, Gateway und ausgehendes Interface beschreiben einen Weiterleitungsweg. Eine Default-Route ist ein Auffangpfad und kein Beweis eines erreichbaren Internets. Ein Gateway muss selbst erreichbar sein. Laufzeitrouten sind nicht automatisch dauerhaft; ein Netzwerkmanager kann sie erneut setzen.

Quelle, am 2026-11-13 gelesen: [net-tools: route-Handbuch](https://man7.org/linux/man-pages/man8/route.8.html)

## 3. Syntax

```text
route [-n] [-4|-6]
route [OPTIONEN] {add|del} ZIEL [PARAMETER]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| Ohne add/del | Routingtabelle anzeigen. |
| `-n` | Numerische Adressen statt Namensauflösung. |
| `-4`, `-6` | Adressfamilie wählen. |
| `-e` | Anzeige im netstat-Format. |
| `add`, `del` | Routing ändern; keine Diagnoseoptionen. |
| `gw`, `dev`, `metric` | Gateway, Gerät und Metrik einer Änderung. |
| `-C` | Historischer Routingcache-Modus; im aktuellen Kernel nicht verfügbar. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
route -n -4
Erfundenes Zielnetz: 192.0.2.0/24
```

Das Muster ist eine numerische IPv4-Anzeige. Das erfundene Präfix wird nicht als neue Route installiert. Eine Route zum Netz verrät noch nicht, welche Anwendung ein Ziel erreicht. Es wurde kein Kernelrouting abgefragt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Altanleitungen prüfen:** Anzeige- und Änderungsformen auseinanderhalten. **Netzpfad verstehen:** Adresskonfiguration, Routing und DNS als getrennte Voraussetzungen betrachten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Änderungen an Default- oder spezifischen Routen können die eigene Sitzung trennen und Verkehr umleiten. reject ist kein vollständiger Firewallersatz. Metrikvorgaben und Einheiten nicht zwischen net-tools und iproute2 übertragen. Keine Routen oder Systemdateien verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Gateway nicht erreichbar | Nächster Hop muss über einen vorhandenen Pfad erreichbar sein. |
| File exists | Änderungsauftrag traf bestehenden Eintrag; nichts löschen, um fortzufahren. |
| Policyroute fehlt | Grenzen der alten Oberfläche; ip rule/tabellenbezogene Anzeige prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ip route` | Moderne Routenobjekte. |
| `ip rule` | Regelbasiertes Routing. |
| `netstat -r` | Ähnliche ältere Anzeige. |

Ausgangsdatensatz 442 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
