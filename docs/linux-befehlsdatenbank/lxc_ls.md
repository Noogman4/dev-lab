---
id: "lxc_ls"
name: "lxc-ls"
command: "lxc-ls"
category: "Virtualisierung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Virtualisierung", "lxc-ls"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 692
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Bestandsabfrage offen"
---

# lxc-ls – Klassische Lxc-Container auflisten

## 1. Kurzbeschreibung

lxc-ls zeigt klassische LXC-Container des gewählten Suchbereichs.

## 2. Was macht der Befehl?

Diese Liste ist keine LXD- oder Incus-Instanzliste. Pfad, Benutzerkontext und Zustandsfilter beeinflussen die Auswahl. -f aktiviert ausführliche Spalten, -F legt deren Auswahl fest. Eine leere Liste ist kein Nachweis, dass auf dem Host keinerlei Container existieren.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://linuxcontainers.org/lxc/manpages/man1/lxc-ls.1.html)

## 3. Syntax

```text
lxc-ls [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -1 | Ein Name je Zeile |
| -f | Ausführliche Spalten |
| -F FORMAT | Spaltenauswahl |
| --running | Laufende Container |
| --stopped | Gestoppte Container |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
lxc-ls -1 --running
```

Werkzeug fehlt; kein realer Containerbestand abgefragt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Auflistung und aktive Containersteuerung unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Konfigurationen können Infrastrukturdetails enthalten. Keine Namespace- oder Netzwerkabfrage als Probelauf ergänzt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Liste leer | Pfad und Rechte prüfen |
| Andere Syntax | LXD-lxc list ist eigenständige Schnittstelle |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Bestandsabfrage offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| lxc-start | Aktiver Start |
| lxc-stop | Aktiver Stop |
| incus | Andere Verwaltung |

Ausgangsdatensatz 692 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
