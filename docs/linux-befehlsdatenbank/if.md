---
id: "if"
name: "if"
command: "if"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "safe"
tags: ["bash builtins", "if"]
status: "Lokale Primärhilfe und Erfolgs-/Leerauswahl praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 88
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# if – Entscheidungen anhand von Befehlsstatus treffen

## 1. Kurzbeschreibung

`if` ist ein Shell-Schlüsselwort für bedingte Abläufe. Es führt einen Zweig aus, wenn eine geprüfte Befehlsliste erfolgreich endet. **Root-Rechte sind für die Sprachkonstruktion nicht nötig.** Die ausgeführten Prüf- und Arbeitsbefehle bestimmen die tatsächlichen Zugriffe.

Es wird nicht das gedruckte Wort „wahr“ betrachtet, sondern ein numerischer Rückgabestatus: 0 ist Erfolg, andere Werte gelten für die Auswahl als Nichterfolg.

## 2. Was macht der Befehl?

Zuerst wird die Bedingung als Befehlsliste ausgeführt. Bei Erfolg folgt der `then`-Teil. Andernfalls werden vorhandene `elif`-Bedingungen der Reihe nach geprüft oder der `else`-Teil erreicht. `fi` schließt die gesamte Auswahl.

Die Primärquelle ist die lokal gelesene Hilfe `help if` aus Bash 5.2.21. Weiterführend: [Bash-Bedingungen](https://www.gnu.org/software/bash/manual/html_node/Conditional-Constructs.html). Die Auswertung ist keine eigene Wahrheitssprache für beliebige Eingaben. Ein einfacher Aufruf `if "$text"` würde versuchen, den Text als Befehlsnamen auszuführen, statt ihn allgemein als Ja-/Nein-Antwort zu interpretieren.

## 3. Syntax

```text
if BEDINGUNG; then
  BEFEHLE_BEI_ERFOLG
elif WEITERE_BEDINGUNG; then
  WEITERE_BEFEHLE
else
  RESTFALL
fi
```

`elif` und `else` sind optional. `then` und der Abschluss sind erforderlich. Eine Bedingung kann beispielsweise der Vergleichsbefehl `[` sein. Dessen abschließendes `]` ist ein eigenes Argument und benötigt passende Leerzeichen.

## 4. Wichtige Optionen

`if` selbst besitzt keine gewöhnlichen Optionen. Wichtige zugehörige Formen:

| Element | Bedeutung | Hinweis |
| --- | --- | --- |
| `[ "$a" = "$b" ]` | Zwei Zeichenketten vergleichen. | Das ist ein test-Aufruf mit eigener Syntax. |
| `[ "$n" -gt 0 ]` | Ganzzahl mit 0 vergleichen. | Eingabe muss zum Zahlenvergleich passen. |
| `! BEFEHL` | Status logisch umkehren. | Kann die ursprüngliche Fehlerdifferenzierung verdecken. |
| `then` | Erfolgszweig beginnen. | Keine zusätzliche Prüfung. |
| `elif` | Weitere Bedingung bei bisherigem Nichterfolg. | Reihenfolge ist entscheidend. |
| `else` | Verbleibenden Fall behandeln. | Kann auch einen unerwarteten Prüffehler erreichen. |

Bash `[[ ... ]]` und arithmetisches `(( ... ))` sind weitere Konstruktionen. Ihre Regeln sind nicht identisch mit `[`; Vergleichsoperatoren und Zitierung nicht blind übertragen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen festen numerischen Wert prüfen

```bash
treffer=2
if [ "$treffer" -gt 0 ]; then
  printf 'Treffer vorhanden\n'
else
  printf 'Keine Treffer\n'
fi
```

Der eigene Übungswert 2 ist größer als 0. Erwartet wird deshalb nur `Treffer vorhanden`. Das Beispiel zählt keinen realen Bestand und verändert keine Datei.

### Schritt 2: Nichterfolg ohne Restfall betrachten

```bash
if false; then
  printf 'Unerwartet\n'
fi
printf 'Auswahlstatus: %s\n' "$?"
```

`false` ist ein bewusst erfolgloser Testbefehl. Der Ausgabebefehl im Zweig wird nicht ausgeführt. Da es weder einen erfolgreichen Zweig noch einen `else`-Teil gibt, endet diese gesamte if-Auswahl in Bash mit Status 0. Erwartet wird `Auswahlstatus: 0`.

### Schritt 3: Rückgabestatus nicht missverstehen

Der Status der gesamten Auswahl ist nicht einfach der Status der ersten Bedingung. Wird ein Zweig ausgeführt, zählt grundsätzlich dessen letzte ausgeführte Anweisung. Weitere Befehle nach `fi` können diesen Status wiederum überschreiben. Eine gewünschte fachliche Fehlermeldung braucht daher einen bewusst gewählten Ablauf und Status.

## 6. Typische Anwendungsfälle

### Vorbedingungen prüfen

Ein Skript prüft eine bekannte Voraussetzung, bevor eine weitere Aktion folgt. Dabei den Prüfbefehl so wählen, dass er tatsächlich die benötigte Eigenschaft untersucht.

### Fehler verständlich behandeln

Ein Arbeitsbefehl wird unmittelbar als Bedingung ausgewertet. Bei Nichterfolg können Meldung und Abbruch folgen. Wenn verschiedene Fehlerwerte wichtig sind, den ursprünglichen Status im passenden Zweig früh sichern.

### Mehrere gültige Zustände unterscheiden

Mit `elif` lassen sich weitere Fälle ergänzen. Bei vielen festen Textwerten kann `case` leichter lesbar sein.

## 7. Risiken, Nebenwirkungen und Vorsicht

Auch die Bedingung ist ein echter Befehl und kann Nebenwirkungen haben. Ein Ausdruck, der einen Download oder eine Änderung startet, wird durch seine Position hinter `if` nicht zu einer rein lesenden Prüfung.

Ein Nichterfolg kann einen erwarteten negativen Zustand oder einen echten Ausführungsfehler bedeuten. Diese Fälle nicht automatisch als gleichwertige Erlaubnis behandeln. Ungeprüfte Eingaben nicht mit `eval` zu Bedingungen machen. Bei Skripten mit `set -e` gelten kontextabhängige Ausnahmen für Bedingungen; nicht allein auf automatischen Abbruch vertrauen.

## 8. Häufige Fehler

- **0 als falsch verstanden:** Shellstatus 0 bedeutet Erfolg.
- **Text statt Befehl verglichen:** Eine Zeichenkette ist nicht automatisch eine Bedingung.
- **Leerzeichen um `[` fehlen:** Argumente des Vergleichsbefehls sind falsch getrennt.
- **Fehler und negativer Treffer gleichgesetzt:** Der Prüfbefehl hat möglicherweise mehrere relevante Statuswerte.
- **Status erst später gelesen:** Andere Befehle haben `$?` bereits verändert.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst feste Daten mit reinen Ausgaben prüfen. Jeden möglichen Zweig und ungültige Eingaben gezielt betrachten. Syntaxprüfung, erfolgreich ausgeführter Zweig und vollständige fachliche Prüfung sind unterschiedliche Nachweise.

**Prüfstand:** Lokale Bash-5.2.21-Hilfe gelesen. Beide vollständigen Beispiele in einer separaten Bash ohne persönliche Startdateien ausgeführt; erwartete Trefferzeile und Auswahlstatus 0. Keine Benutzerdateien verändert. Externe Prüffehler, komplexe Befehlslisten und konkrete `set -e`-Sonderfälle nicht praktisch geprüft.

## 10. Verwandte Befehle

- `then`, `elif`, `else`, `fi`: Bestandteile derselben Auswahl.
- `test`, `[`: Vergleichsbefehle.
- `case`: Auswahl anhand von Textmustern.
- `return`, `exit`: Ablauf mit bewusst gesetztem Status verlassen.

Ausgangseintrag: Datensatz 88 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
