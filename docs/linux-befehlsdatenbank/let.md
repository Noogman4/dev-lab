---
id: "let"
name: "let"
command: "let"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "caution"
tags: ["bash builtins", "let"]
status: "Lokale Primärhilfe sowie Nichtnull-/Nullausdruck praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 90
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# let – Ganzzahlarithmetik und ihren Rückgabestatus verstehen

## 1. Kurzbeschreibung

`let` ist ein Bash-Builtin zur Auswertung arithmetischer Ausdrücke. Es arbeitet mit Ganzzahlen und kann Variablen verändern. **Root-Rechte sind nicht nötig.** Ein berechneter Zahlenwert ist nicht dasselbe wie der Rückgabestatus des Aufrufs.

Für einfache Zuweisungen kann die Schreibweise `summe=$((2 + 3))` übersichtlicher sein. Die Regeln der Shellarithmetik gelten dabei weiterhin; sie ist keine sichere allgemeine Auswertung beliebiger Benutzereingaben.

## 2. Was macht der Befehl?

Jedes übergebene Argument wird als eigener arithmetischer Ausdruck ausgewertet. Zuweisungen ändern Variablen der laufenden Shell. Innerhalb des Ausdrucks können Variablennamen ohne führendes Dollarzeichen verwendet werden.

Die Auswertung nutzt Ganzzahlen begrenzter Breite; Überlauf wird nicht allgemein als Fehler gemeldet. Division durch 0 ist dagegen ein Fehler. Lokale Primärquelle ist `help let` aus Bash 5.2.21. Weiterführend: [Bash-Arithmetik](https://www.gnu.org/software/bash/manual/html_node/Shell-Arithmetic.html).

Der Status richtet sich nach dem **Wert des letzten Ausdrucks**: Wert 0 ergibt Status 1, ein von 0 verschiedener Wert Status 0. Eine korrekt berechnete Null ist deshalb kein gewöhnlicher Rechenfehler.

## 3. Syntax

```text
let AUSDRUCK [WEITERER_AUSDRUCK ...]
let 'summe = 2 + 3'
```

Ausdrücke mit Leerzeichen zitieren, damit sie jeweils ein Shellargument bleiben. Die Anführungszeichen begrenzen die Shellverarbeitung, schalten aber die arithmetische Interpretation nicht aus. Es gibt keine allgemeine `let --help`-Programmschnittstelle; in Bash `help let` verwenden.

## 4. Wichtige Optionen

Es geht um Operatoren, nicht um eine gewöhnliche Optionsliste:

| Ausdruck | Bedeutung | Grenze |
| --- | --- | --- |
| `a = 5` | Variable zuweisen. | Ändert den laufenden Shellzustand. |
| `a + b`, `a - b` | Addition und Subtraktion. | Ganzzahlarithmetik begrenzter Breite. |
| `a * b`, `a / b` | Multiplikation und Division. | Ganzzahldivision, kein beliebiger Dezimalrechner. |
| `a % b` | Divisionsrest. | Nenner darf nicht 0 sein. |
| `a += 2` | Wert erhöhen und zuweisen. | Ausgangswert wird arithmetisch interpretiert. |
| `a++` | Nachinkrement. | Ausdruckswert ist der alte Wert. |
| `++a` | Vorinkrement. | Ausdruckswert ist der neue Wert. |
| `(a + b) * c` | Reihenfolge gruppieren. | Gesamten Ausdruck als Argument zitieren. |

Eine führende 0 kann eine Oktalzahl kennzeichnen. Deshalb ist etwa ein ungeprüft übernommener Text mit führenden Nullen nicht automatisch die erwartete Dezimalzahl. Auch Basispräfixe ersetzen keine vollständige Eingabeprüfung.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine einfache Summe bilden

```bash
let 'summe = 2 + 3'
printf 'Summe: %s\n' "$summe"
```

Erwartet wird `Summe: 5`. Der Ausdruck setzt die Variable; `let` selbst muss den Zahlenwert nicht als Text ausgeben. Das übernimmt `printf`.

### Schritt 2: Nullwert und Status getrennt betrachten

```bash
let 'null = 0'
status=$?
printf 'Wert: %s; Status: %s\n' "$null" "$status"
```

Erwartet wird `Wert: 0; Status: 1`. Der Status wird direkt nach `let` gesichert, bevor `printf` ihn verändern kann. Die Zuweisung des Zahlenwerts 0 war beabsichtigt und ist kein fehlgeschlagenes Setzen der Variable.

### Schritt 3: Strenge Fehlerbehandlung berücksichtigen

Dieses Beispiel wird ohne `set -e` ausgeführt. In einem Skript mit dieser Einstellung kann ein statusliefernder Nullausdruck je nach Kontext einen Abbruch auslösen. Besonders Nachinkrement von einem Ausgangswert 0 wird deshalb häufig missverstanden. Nicht jeden Status 1 pauschal mit „Rechenfehler“ gleichsetzen.

## 6. Typische Anwendungsfälle

### Eigene Zähler verwalten

Zählwerte in überschaubaren Schleifen erhöhen. Den Rückgabestatus des Ausdrucks nicht unbeabsichtigt als Erfolg der gesamten fachlichen Verarbeitung verwenden.

### Ganzzahlige Größen berechnen

Kleine feste Werte kombinieren, etwa eine Anzahl von Testschritten. Einheiten, Bereich und mögliche Überläufe müssen zum Anwendungsfall passen.

### Bedingungen berechnen

Ein Ausdruck kann einen numerischen Wahrheitswert liefern. Für Text-, Datei- und Berechtigungsprüfungen sind andere passende Vergleichsmechanismen nötig.

## 7. Risiken, Nebenwirkungen und Vorsicht

Shellarithmetik darf nicht mit beliebigem unkontrolliertem Text gefüttert werden. Variablenwerte können erneut als Ausdrücke interpretiert werden; komplexe Auswertungen und Arrays bringen weitere Gefahren mit. Quoting allein macht diesen Datenkanal nicht sicher. Eingaben vorher nach erlaubtem Zahlenformat und Bereich prüfen.

Überläufe, unerwartete Zahlbasis und Ganzzahldivision können fachlich falsche Ergebnisse liefern, ohne dass ein normaler Ausführungsfehler gemeldet wird. Geänderte Variablen bleiben in der Shell erhalten. Für genaue Dezimal- oder sehr große Rechnungen ein geeignetes anderes Werkzeug und dessen Eingabesicherheit wählen.

## 8. Häufige Fehler

- **Status 1 trotz korrekt berechneter Null:** Das ist die dokumentierte Wert-/Statusregel.
- **Leerzeichen teilen den Ausdruck:** Argument war nicht zitiert.
- **Nachkommateil fehlt:** Ganzzahldivision verwendet.
- **Zahl mit führender Null scheitert:** Zahlbasis und erlaubte Ziffern prüfen.
- **`set -e` beendet den Ablauf:** Nullwert des Ausdrucks und konkreten Fehlerbehandlungskontext untersuchen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Feste kleine Zahlen verwenden, Ergebnis und Status getrennt anzeigen und Arbeitsvariablen bewusst benennen. Fremde Texte nicht als Rechenausdrücke übernehmen. Für einfache Zuweisungen die lesbare arithmetische Expansion erwägen und deren Wertebereich ebenfalls verstehen.

**Prüfstand:** Bash 5.2.21 und lokale let-Hilfe gelesen. Summe 5 sowie Nullwert mit Status 1 in einer getrennten Bash ohne persönliche Startdateien geprüft. Keine Benutzerdateien verändert. Überlauf, Divisionfehler, fremde Eingaben und konkrete `set -e`-Abbruchfälle nicht praktisch geprüft.

## 10. Verwandte Befehle

- `$(( ... ))`: arithmetischen Wert als Shelltext expandieren.
- `(( ... ))`: Bash-Arithmetikkonstrukt mit ähnlicher Statusregel.
- `declare -i`, `typeset -i`: Variablen arithmetische Attribute geben.
- `bc`: andere Rechenumgebung mit eigener Syntax und Voraussetzungen.

Ausgangseintrag: Datensatz 90 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
