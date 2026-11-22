---
id: "expr"
name: "expr"
command: "expr"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["expr", "grundlagen & hilfe"]
status: "Multiplikation und Nullergebnis lokal geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 353
reviewed_at: "2026-11-13"
locally_checked_version: "GNU-coreutils-Manpage 9.4; zwei Rechenfälle geprüft"
---

# expr – einfache Ausdrücke aus einzelnen Argumenten auswerten

## 1. Kurzbeschreibung

`expr` wertet einfache Zahlen-, Vergleichs- oder Zeichenkettenausdrücke aus. Die Bestandteile werden als getrennte Argumente übergeben. **Root-Rechte sind nicht nötig.**

## 2. Was macht der Befehl?

Grundlage ist die lokale GNU-Manpage. Das Ergebnis wird ausgegeben; der Rückgabestatus enthält zusätzlich eine Bewertung. Eine errechnete Null ist dabei kein gewöhnlicher technischer Fehler.

Viele Operatoren haben auch eine Shellbedeutung. Deshalb müssen sie gegebenenfalls quotiert werden. `expr` sieht nur die Argumente, die nach der Shellverarbeitung tatsächlich übrig bleiben.

## 3. Syntax

```bash
expr 7 '*' 6
expr 5 - 5
expr length 'NetMon'
```

Zwischen Operanden und Operator stehen getrennte Argumentgrenzen. `expr 7+6` ist nicht derselbe Rechenauftrag wie `expr 7 + 6`.

## 4. Wichtige Optionen

| Form | Aufgabe | Grenze |
| --- | --- | --- |
| `A + B`, `A - B` | Ganzzahlige Summe oder Differenz. | Keine allgemeine Dezimalrechnung. |
| `A '*' B` | Multiplikation. | Stern vor Shellglobbing schützen. |
| `A / B` | Ganzzahlige Division. | Null als Divisor ist unzulässig. |
| `length TEXT` | Zeichenkettenlänge bestimmen. | GNU-Funktion; Plattform beachten. |
| `TEXT : MUSTER` | Verankerten regulären Ausdruck prüfen. | Nicht dieselbe Sprache wie Shellwildcards. |
| `--help` | Bedienung zeigen. | Separater Hilfsaufruf. |

Größen- und Darstellungsgrenzen der lokalen Implementierung beachten. Für komplexe Mathematik ist ein passender Rechner geeigneter.

## 5. Beispiel erklärt Schritt für Schritt

```bash
expr 7 '*' 6
```

Die drei Argumente sind `7`, `*` und `6`. Die einfachen Anführungszeichen verhindern, dass die Shell den Stern in Dateinamen umsetzt. Lokal wurde `42` mit Status `0` ausgegeben.

Daneben wurde `expr 5 - 5` geprüft: Ausgabe `0`, Status `1`. Dieser Status bedeutet hier das Nullergebnis. Eine automatische Fehlerbehandlung, die jede Nichtnull als technischen Defekt meldet, wäre unpassend.

Die Manpage unterscheidet außerdem Status `2` für ungültige Syntax und `3` für einen Fehler. Diese Fälle wurden nicht absichtlich provoziert.

## 6. Typische Anwendungsfälle

- Einfache vorhandene Shellskripte verstehen.
- Kleine ganzzahlige Ausdrücke berechnen.
- Einfache Zeichenkettenoperationen auswerten.
- Ergebniswert und Status bewusst getrennt behandeln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der normale Aufruf berechnet und gibt aus. Fehler können aber durch Shelloperatoren entstehen: Ein unquotiertes `>` wäre möglicherweise eine Umleitung statt eines Vergleichsoperators.

Ungeprüfte Eingaben nicht zu Shellcode zusammensetzen. Für Rechenlogik im Skript Eingabeformat und Wertebereich festlegen.

## 8. Häufige Fehler

- **Operator ohne Leerzeichen:** Falsche Argumentstruktur.
- **Stern unquotiert:** Dateinamensexpansion statt Multiplikation.
- **Nullergebnis als Rechenabbruch:** Statussemantik beachten.
- **Dezimalzahlen erwartet:** Werkzeug ist kein allgemeiner Taschenrechner.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit festen Zahlen beginnen. Bei eigenen Bashskripten kann `$(( ... ))` die ganzzahlige Arithmetik übersichtlicher machen; auch dort sind Eingaben bewusst zu behandeln.

Für jede Statusauswertung zuerst die konkrete Programmbedeutung lesen. Ein universelles Schema „Nichtnull gleich kaputt“ ist hier nicht ausreichend.

## 10. Verwandte Befehle

- `test`: Bedingungen ohne allgemeine Ergebnisausgabe.
- `printf`: Zahlen und Texte formatieren.
- `bc`: Rechner mit weitergehender Arithmetik, soweit installiert.
- Bash-Arithmetik: Interpreterinterne Ganzzahlausdrücke.

**Prüfstand:** Zwei feste Rechenfälle lokal geprüft. Keine Dateien oder Systemeinstellungen verändert.

Ausgangsdatensatz 353 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
