---
id: "lxd"
name: "lxd"
command: "lxd"
category: "Virtualisierung"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Virtualisierung", "lxd"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 695
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Serverbetrieb offen"
---

# lxd – Lxd als Server statt Client einordnen

## 1. Kurzbeschreibung

lxd ist die Serverkomponente der LXD-Container- und VM-Verwaltung.

## 2. Was macht der Befehl?

Der Client heißt üblicherweise lxc. Ein direkter Serverstart oder eine Initialisierung ist kein Diagnoseaufruf. Serverkonfiguration umfasst unter anderem Storage, Netzwerke und Zugriffsberechtigungen. Der in der Herstellerdokumentation erklärte Aufbau wird hier von den klassischen LXC-Werkzeugen getrennt.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://canonical.com/lxd/docs/latest/explanation/lxd_lxc/)

## 3. Syntax

```text
lxd [OPTIONEN] [UNTERBEFEHL]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --help | Lokale Serverschnittstelle lesen |
| init | Server einrichten, reale Änderung |
| lxc list | Separate Clientabfrage, kein lxd-Unterbefehl |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
lxd --help
```

Der Server ist nicht installiert. Kein Daemon gestartet, kein Socket geöffnet und keine Initialisierung durchgeführt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Client und Dienst in Installationsanleitungen auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Serverzugang erlaubt weitreichende Instanz- und Hostverwaltung. Keine Mitgliedschaften oder privilegierten Sockets für einen Test freigeben.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| lxd fehlt | Clientinstallation beweist keine Serverinstallation |
| Initialisierung verlangt Storage | Das ist aktive Einrichtung, keine Hilfe |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Serverbetrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| lxc | LXD-Client |
| incus | Andere Familie |
| lxc-create | Klassische LXC-Definition |

Ausgangsdatensatz 695 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
