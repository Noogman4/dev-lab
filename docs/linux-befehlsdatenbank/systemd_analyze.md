---
id: "systemd_analyze"
name: "systemd-analyze"
command: "systemd-analyze"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "systemd-analyze"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 616
reviewed_at: "2026-11-13"
locally_checked_version: "systemd 255.4-1ubuntu8.18"
---

# systemd-analyze – Systemd-Analysemodi gezielt auswählen

## 1. Kurzbeschreibung

systemd-analyze bündelt Startzeitanalyse und weitere Diagnose- beziehungsweise Parserfunktionen.

## 2. Was macht der Befehl?

blame und critical-chain lesen Managerdaten; parallele Starts machen blame nicht zu einer addierbaren Bootdauer. timespan verarbeitet dagegen eine Dauerzeichenfolge offline. Eine Security-Bewertung ist eine Konfigurationsheuristik, kein allgemeines Sicherheitszertifikat.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/systemd-analyze.1.html)

## 3. Syntax

```text
systemd-analyze [OPTIONEN] UNTERBEFEHL [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| blame | Unit-Aktivierungszeiten |
| critical-chain | Zeitkritische Kette |
| timespan TEXT | Dauer interpretieren |
| verify DATEI | Unitprüfung mit eigener Aussagegrenze |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
LC_ALL=C systemd-analyze timespan '1min 2s' > result.txt
cat result.txt
grep -q '62000000' result.txt
printf 'Eigene Dauerzeichenfolge geprueft\n'
```

### Schritt 3: Ergebnis einordnen

62 Sekunden entsprechen 62000000 Mikrosekunden. Nur dieser Textparser wurde geprüft, keine Bootanalyse, Unit oder Securitybewertung. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Dauerwerte verstehen; Diagnosemodus vor Aufruf auswählen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Unterbefehle haben unterschiedliche Zugriffswege. Keine Manager- oder Hardwareabfrage zum Funktionsnachweis.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Ungültige Dauer | Einheit und Syntax prüfen |
| Blame summiert zu viel | Parallelität berücksichtigen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** systemd 255.4-1ubuntu8.18. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| systemctl | Manager |
| systemd-escape | Andere Textumwandlung |
| time | Reale Laufzeit |

Ausgangsdatensatz 616 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
