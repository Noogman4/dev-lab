---
id: "w"
name: "w"
command: "w"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "w"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 619
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Funktionsprüfung offen"
---

# w – Sitzungs- und Prozessinformationen einordnen

## 1. Kurzbeschreibung

w kombiniert Sitzungsinformationen mit Aktivitäts- und CPU-Angaben.

## 2. Was macht der Befehl?

JCPU und PCPU sind verschiedene Zeitgrößen; Idle ist keine zuverlässige Messung menschlicher Abwesenheit. Sitzungsquellen unterscheiden sich nach Version. Eine leere Anzeige beweist nicht, dass keine Benutzerprozesse existieren.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/w.1.html)

## 3. Syntax

```text
w [OPTIONEN] [BENUTZER]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -h | Kopfzeile ausblenden |
| -s | Kurzformat |
| -f | Hostfeld umschalten |
| -i | Numerische Adressen statt Namen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
w -h -s TESTBENUTZER
```

Es werden keine echten Sitzungen oder Befehlszeilen abgefragt. Der Benutzername bleibt ein Platzhalter.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Sitzungsquelle und Aktivität getrennt verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Befehlszeilen und Anmeldeorte können vertraulich sein. Kein Terminalgerät für eine alternative Erkennung gescannt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Benutzer fehlt | Sitzungsquelle kann unvollständig sein |
| Hohe JCPU | Mehrere tty-Prozesse können beitragen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| who | Sitzungen |
| ps | Prozesse |
| last | Historie |

Ausgangsdatensatz 619 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
