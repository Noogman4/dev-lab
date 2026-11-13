---
id: "lxc"
name: "lxc"
command: "lxc"
category: "Virtualisierung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Virtualisierung", "lxc"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 690
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; LXD-Clientbetrieb offen"
---

# lxc – Lxd-Client lxc von Lxc-Einzelwerkzeugen trennen

## 1. Kurzbeschreibung

lxc bezeichnet hier den Client von LXD, nicht den Server und nicht lxc-create.

## 2. Was macht der Befehl?

Unterbefehle wie list, launch und exec gehören zur LXD-API. Die klassisch benannten Werkzeuge lxc-create und lxc-start haben eine andere Schnittstelle und Konfiguration. Remote, Projekt und Profil bestimmen den Wirkungskontext.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://canonical.com/lxd/docs/latest/reference/manpages/lxc/)

## 3. Syntax

```text
lxc [OPTIONEN] UNTERBEFEHL [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| list | Instanzliste |
| info NAME | Instanzinformationen |
| launch | Anlegen und Starten |
| exec | Befehl in Instanz |
| --project NAME | Projekt wählen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
lxc list
```

Der LXD-Client fehlt; keine Verbindung zu einem lokalen oder entfernten Server hergestellt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Ähnliche Containernamen in Anleitungen eindeutig zuordnen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein Container ist keine automatisch vollständige Sicherheitsgrenze. Start und Dateifreigaben können Host- und Netzwerkzustand verändern. Keine Containeraktionen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| lxc-create-Syntax scheitert | Nicht dieselbe CLI |
| Name fehlt | Remote und Projekt prüfen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; LXD-Clientbetrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| lxd | Server |
| incus | Andere Client-/Serverfamilie |
| lxc-start | Klassische LXC-CLI |

Ausgangsdatensatz 690 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
