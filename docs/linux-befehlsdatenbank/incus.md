---
id: "incus"
name: "incus"
command: "incus"
category: "Virtualisierung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Virtualisierung", "incus"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 689
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Server und Instanzen offen"
---

# incus – Incus-Client und Serverkontext unterscheiden

## 1. Kurzbeschreibung

incus verwaltet Container und virtuelle Maschinen über einen Incus-Server.

## 2. Was macht der Befehl?

Remote, Projekt und Instanzname legen den Verwaltungsbereich fest. list ist eine Serverabfrage; launch erzeugt und startet, exec führt Code in Instanzen aus. Ein Benutzer mit Serverzugang kann umfangreiche Hostressourcen verwalten.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://linuxcontainers.org/incus/docs/main/reference/manpages/incus/)

## 3. Syntax

```text
incus [OPTIONEN] UNTERBEFEHL [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| list | Instanzen abfragen |
| info NAME | Details |
| launch | Erzeugen und starten |
| exec | Programm in Instanz |
| --project NAME | Verwaltungsprojekt wählen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
incus list
```

Keine reale Serververbindung, Instanz oder Konfiguration geprüft. Incus fehlt lokal.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Verwaltungskontext vor späteren Einzelaktionen verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Images können aus dem Netz geladen werden. Privilegierte Instanzen, Storage und Gerätefreigaben betreffen den Host. Keine Initialisierung oder Instanzerzeugung.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Server nicht erreichbar | Remote und Berechtigung prüfen, keinen Dienst starten |
| Instanz fehlt | Projekt und Remote beachten |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Server und Instanzen offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| lxc | LXD-Client im eigenen Kontext |
| lxc-create | Klassische LXC-Werkzeuge |
| virsh | Andere Verwaltung |

Ausgangsdatensatz 689 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
