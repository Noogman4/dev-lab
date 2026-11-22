---
id: "netstat"
name: "netstat"
command: "netstat"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "safe"
tags: ["Netzwerk Grundlagen", "netstat"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 434
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# netstat – Socketanzeigen und Erreichbarkeit auseinanderhalten

## 1. Kurzbeschreibung

netstat aus net-tools zeigt unter anderem Sockets, Routen und Interfacezähler. Für neue Anleitungen verweist sein Handbuch auf ss beziehungsweise die passenden ip-Unterbefehle.

## 2. Was macht der Befehl?

Ein lauschender TCP-Socket bedeutet lokale Empfangsbereitschaft, nicht externe Erreichbarkeit durch Firewalls und Routing. UDP hat nicht dieselben Verbindungszustände wie TCP. Prozesszuordnungen können fehlen, wenn Rechte oder Lebensdauer der Prozesse keine Sicht erlauben. Eine Tabelle ist eine Momentaufnahme, keine Ereignishistorie.

Quelle, am 2026-11-13 gelesen: [net-tools: netstat-Handbuch](https://man7.org/linux/man-pages/man8/netstat.8.html)

## 3. Syntax

```text
netstat [OPTIONEN]
netstat {-r|-i|-s} [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-t`, `-u` | TCP- beziehungsweise UDP-Sockets auswählen. |
| `-l` | Lauschende Sockets; standardmäßig ausgelassen. |
| `-a` | Auch lauschende Sockets berücksichtigen. |
| `-n` | Adressen, Ports und Benutzer numerisch anzeigen. |
| `-p` | Prozesszuordnung versuchen; eingeschränkte Sicht möglich. |
| `-r`, `-i`, `-s` | Routen, Interfaces beziehungsweise Protokollstatistiken. |
| `-c` | Wiederholt anzeigen; bleibt laufend. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
netstat -lnt
Erfundene Bindung: 127.0.0.1:8080
```

Das Muster wählt lauschende TCP-Sockets und numerische Ausgabe. Die erfundene Loopback-Bindung wäre lokal gebunden; daraus folgt keine Freigabe über eine externe Adresse. Es wurden keine echten Sockets oder Prozesse ausgelesen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Anleitungen einordnen:** Optionen nach Socket-, Routen- oder Statistikmodus unterscheiden. **Dienstdiagnose planen:** Bindeadresse und Port zusammen mit dem Netzwerkpfad betrachten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Namensauflösung kann zusätzliche Abfragen erzeugen; -n vermeidet diese symbolische Anzeige. Prozessnamen sind kein Identitäts- oder Vertrauensnachweis. Tabellen können interne Adressen und Dienste offenlegen. Keine Dienste wurden gestartet oder verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Listener fehlt | Ohne -l/-a wird er möglicherweise ausgeblendet. |
| PID/Name ist - | Rechte, Kernelzuordnung oder bereits beendeten Prozess berücksichtigen. |
| Portname statt Nummer | -n verwenden und Protokollfamilie klar wählen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ss` | Moderner Socketbericht. |
| `ip route` | Routentabellen. |
| `ip -s link` | Linkzähler getrennt vom Socketbericht. |

Ausgangsdatensatz 434 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
