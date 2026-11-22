---
id: "lxc_create"
name: "lxc-create"
command: "lxc-create"
category: "Virtualisierung"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Virtualisierung", "lxc-create"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 691
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Erzeugung und Templates offen"
---

# lxc-create – Eine klassische Lxc-Containerdefinition anlegen

## 1. Kurzbeschreibung

lxc-create erstellt einen klassischen LXC-Container mitsamt Konfiguration und möglichem Rootdateisystem.

## 2. Was macht der Befehl?

-t wählt ein Template; weitere Templateargumente folgen nach --. Templates können ausführbaren Code, Downloads und Storageoperationen auslösen. Erzeugen ist von Starten zu unterscheiden und dennoch eine reale Zustandsänderung.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://linuxcontainers.org/lxc/manpages/man1/lxc-create.1.html)

## 3. Syntax

```text
lxc-create -n NAME -t TEMPLATE [OPTIONEN] [-- TEMPLATEOPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -n NAME | Containername |
| -t TEMPLATE | Erzeugungsvorlage |
| -f DATEI | Konfiguration |
| -B BACKEND | Speicherbackend |
| -P PFAD | Containerbasis, versionsabhängig |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
lxc-create -n EIGENER_TESTNAME -t GEPRUEFTES_TEMPLATE
```

Keine Vorlage ausgeführt, kein Image geladen und kein Containerverzeichnis angelegt. Das Werkzeug fehlt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Template, Definition und laufenden Container auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Rootdateisysteme und Backendoptionen können erheblich schreiben. Unprivilegierter Betrieb hängt von vorbereiteten Rechten ab; keine solchen Systemvoraussetzungen geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Template fehlt | Passende Installation und Herkunft prüfen |
| Permission denied | Keine pauschale Rechteerhöhung |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Erzeugung und Templates offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| lxc-start | Startet Definition |
| lxc-ls | Bestand |
| lxc | Anderer LXD-Client |

Ausgangsdatensatz 691 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
