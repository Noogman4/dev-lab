---
id: "pmap"
name: "pmap"
command: "pmap"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "pmap"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 502
reviewed_at: "2026-11-13"
locally_checked_version: "procps-ng 4.0.4"
---

# pmap – Speicherabbildungen eines Prozesses lesen

## 1. Kurzbeschreibung

pmap zeigt die virtuellen Speicherbereiche einer angegebenen PID.

## 2. Was macht der Befehl?

Die Ausgabe verbindet Adressbereiche, Zugriffsrechte und Zuordnungen zu Dateien oder anonymem Speicher. Virtuelle Größe ist keine Aussage über tatsächlich belegten RAM. RSS bezeichnet residente Seiten; PSS verteilt gemeinsam verwendete Seiten anteilig. Ein Vergleich mehrerer Prozesse muss diese Unterschiede berücksichtigen. Die Sicht ist eine Momentaufnahme und hängt von /proc sowie Zugriffsrechten ab.

Quelle, am 2026-11-13 gelesen: [pmap-Handbuch](https://man7.org/linux/man-pages/man1/pmap.1.html), [Kernel-Manpage smaps](https://man7.org/linux/man-pages/man5/proc_pid_smaps.5.html)

## 3. Syntax

```text
pmap [OPTIONEN] PID ...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -x | Erweiterte Tabelle mit Speicherkennzahlen. |
| -d | Gerätebezogene Darstellung. |
| -q | Kopf- und Fußzeilen unterdrücken. |
| -p | Vollständige Pfade anzeigen. |
| -X, -XX | Zusätzliche smaps-Daten; Spalten versions- und kernelabhängig. |
| -n, -N DATEI | Konfiguration schreiben; deshalb ist nicht jeder Modus rein lesend. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
pmap --version
pmap -x "$$" > maps.txt
test -s maps.txt
head -n 4 maps.txt
printf 'Eigene Speicherkarte gelesen
'
```

### Schritt 3: Ergebnis einordnen

Die PID gehört der neu gestarteten Übungsshell. Die Prüfung bestätigt eine nichtleere Speicherkarte, nicht eine feste RAM-Menge. Adressen und Messwerte ändern sich bei jedem Lauf. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Speicherbereiche einer eigenen Anwendung einordnen; Dateizuordnungen und anonymen Speicher unterscheiden; Diagnosewerte mit smaps vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Pfade und Prozessnamen können vertraulich sein. Keine fremden Speicherinhalte auslesen. Selbst große virtuelle Bereiche sind noch kein Speicherleck. Konfigurationsschreiboptionen gesondert behandeln.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| PID verschwunden | Prozess endete zwischen Auswahl und Abfrage. |
| Zugriff verweigert | /proc-Schutz oder Berechtigungen begrenzen die Sicht. |
| Spalten anders | -X ist nicht als stabiles Austauschformat garantiert. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** procps-ng 4.0.4. Praktisch geprüft: Eigene Shell lesend geprüft; andere PIDs, Konfigurationsschreiben und Rechtefälle offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| ps | Kompakte Prozesskennzahlen. |
| free | Systemweiter Speicherüberblick. |
| top | Wiederholte Prozessbeobachtung. |

Ausgangsdatensatz 502 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
