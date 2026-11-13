---
id: "who"
name: "who"
command: "who"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "who"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 620
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Funktionsprüfung offen"
---

# who – Sitzungsdaten statt eigener Identität anzeigen

## 1. Kurzbeschreibung

who zeigt Sitzungsinformationen aus einer Utmp-artigen Datenquelle.

## 2. Was macht der Befehl?

who und whoami beantworten unterschiedliche Fragen. Eine alternative Datei muss zum erwarteten binären Format passen. am i bezieht sich auf den Terminalkontext und ist keine universelle Identitätsprüfung. --lookup kann DNS verwenden.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/who.1.html)

## 3. Syntax

```text
who [OPTIONEN] [DATEI]
who am i
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -H | Spaltenkopf |
| -u | Zusätzliche Sitzungsfelder |
| -b | Letzten Boot anzeigen |
| -q | Namen und Zahl |
| --lookup | Namensauflösung, potenziell Netzwerk |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
who -H EIGENE_UTMP_DATEI
```

Mangels eigener Sitzungsfixture bleibt das Muster unausgeführt. Keine reale Utmp-Datei und keine Anmeldeorte gelesen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Benutzeridentität und registrierte Sitzung auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Fehlende Sitzungsdatensätze sind kein Beweis fehlender Prozesse. Keine Protokolle oder Terminalgeräte verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Leere Anzeige | Quelle oder Sitzungsregistrierung prüfen |
| am i leer | Kein passender Terminalkontext |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| whoami | Effektiver Benutzer |
| id | Identität |
| last | Loginhistorie |

Ausgangsdatensatz 620 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
