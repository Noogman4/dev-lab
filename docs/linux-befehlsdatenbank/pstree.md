---
id: "pstree"
name: "pstree"
command: "pstree"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "pstree"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 505
reviewed_at: "2026-11-13"
locally_checked_version: "PSmisc 23.7"
---

# pstree – Prozessbeziehungen als Baum lesen

## 1. Kurzbeschreibung

pstree ordnet sichtbare Prozesse nach ihren Elternbeziehungen.

## 2. Was macht der Befehl?

Gleiche Teilbäume können zusammengefasst werden; Threads erscheinen in geschweiften Klammern. Eine PID als Argument setzt die Wurzel des dargestellten Teilbaums. Der Baum erklärt Abstammung, keine CPU-Auslastung und keine Dienstabhängigkeiten. Fehlende Namen können aus eingeschränkter /proc-Sicht entstehen.

Quelle, am 2026-11-13 gelesen: [PSmisc pstree-Handbuch](https://man7.org/linux/man-pages/man1/pstree.1.html)

## 3. Syntax

```text
pstree [OPTIONEN] [PID oder BENUTZER]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -p | PIDs anzeigen; verhindert die übliche Zusammenfassung. |
| -A | ASCII-Zeichen für die Baumlinien. |
| -n | Geschwister nach PID ordnen. |
| -a | Argumente anzeigen; mögliche vertrauliche Inhalte. |
| -s | Eltern des gewählten Prozesses einbeziehen. |
| -T | Threads ausblenden. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
pstree -A -p "$$" > tree.txt
cat tree.txt
grep -Fq "($$)" tree.txt
printf 'Eigener Teilbaum gelesen
'
```

### Schritt 3: Ergebnis einordnen

Geprüft wird nur, dass die eigene Shell im gewählten Teilbaum erscheint. Kurzlebige Kinder können je nach Zeitpunkt sichtbar sein oder bereits fehlen. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Eltern-Kind-Beziehungen verstehen; mehrere Worker einer eigenen Anwendung auseinanderhalten; die Herkunft eines bekannten Prozesses nachvollziehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Argumentlisten nicht ungeprüft weitergeben. Ein Elternprozess ist nicht automatisch für alle sichtbaren Kinder fachlich verantwortlich. Kein Signal und keine Prioritätsänderung wird durch die Übung ausgelöst.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Fragezeichen statt Name | Sichtbarkeit oder Zugriffsrechte begrenzt. |
| Weniger Zweige als erwartet | Kompaktierung, Threads und beendete Kinder beachten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** PSmisc 23.7. Praktisch geprüft: Eigener Teilbaum geprüft; fremde Prozesse und Namespacewechsel offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| ps | Einzelne Felder statt Baum. |
| pgrep | Auswahl nach Kriterien. |
| systemctl | Dienstzustand getrennt untersuchen. |

Ausgangsdatensatz 505 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
