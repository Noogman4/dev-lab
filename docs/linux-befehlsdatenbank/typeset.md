---
id: "typeset"
name: "typeset"
command: "typeset"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "caution"
tags: ["bash builtins", "typeset"]
status: "Lokale typeset-/declare-Hilfe sowie Ganzzahl- und Arraybeispiel praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 95
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# typeset – Bash-Variablen mit ausdrücklich gewählten Attributen anlegen

## 1. Kurzbeschreibung

`typeset` ist in Bash ein Synonym für `declare`. Es legt Variablen an, setzt Werte und steuert Attribute wie Ganzzahl, Array oder Schreibschutz. **Root-Rechte sind nicht nötig.** Änderungen betreffen zunächst den Zustand der ausführenden Shell.

Andere Shells besitzen teilweise ebenfalls `typeset`, aber nicht in jeder Einzelheit dieselben Regeln. Diese Dokumentation beschreibt ausdrücklich Bash 5.2.

## 2. Was macht der Befehl?

Attribute beeinflussen spätere Zuweisungen und die Darstellung einer Variable. Eine Ganzzahlvariable interpretiert Zuweisungen arithmetisch; ein Array hält mehrere Elemente getrennt. Das bedeutet mehr als eine bloße erklärende Typbeschriftung.

Innerhalb einer Bash-Funktion erzeugt die Deklaration normalerweise lokale Variablen. `-g` verlangt dort eine globale Deklaration. Namensreferenzen mit `-n` zeigen wiederum auf eine andere Variable und benötigen besonders sorgfältige Namenswahl. Primärquellen sind die lokal gelesenen Hilfen `help typeset` und `help declare`. Weiterführend: [Bash-Builtins](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html).

## 3. Syntax

```text
typeset [OPTIONEN] NAME[=WERT] ...
typeset -p NAME ...
```

Leerzeichen um das Gleichheitszeichen einer einfachen Zuweisung gehören nicht beliebig hinein. Werte mit Leerzeichen passend zitieren. Ohne Namen kann eine Anzeige sehr viele Variablen und deren Werte umfassen; für Diagnose deshalb konkrete Namen bevorzugen.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkrete Grenze |
| --- | --- | --- |
| `-p NAME` | Attribute und Wert gezielt anzeigen. | Kann vertrauliche Werte offenlegen. |
| `-i` | Ganzzahlattribut setzen. | Zuweisungen werden als Rechenausdrücke ausgewertet. |
| `-a` | Indiziertes Array deklarieren. | Numerische Indizes, nicht beliebige Schlüsselnamen. |
| `-A` | Assoziatives Array deklarieren. | Unterstützte Bash-Version voraussetzen. |
| `-r` | Variable schreibgeschützt machen. | Lässt sich nicht einfach mit +r zurücknehmen. |
| `-x` | Variable für Kindprozesse exportieren. | Kein allgemeines Serialisieren von Arrays. |
| `-g` | Innerhalb einer Funktion global deklarieren. | Kann äußeren Zustand bewusst verändern. |
| `-n` | Namensreferenz anlegen. | Wirkung trifft die referenzierte Variable. |
| `-l`, `-u` | Kleinschreibung beziehungsweise Großschreibung bei Zuweisung. | Nicht mit lokaler Gültigkeit verwechseln. |

Für manche Attribute kann die entsprechende Plusform sie ausschalten. Das ist keine universelle Umkehrfunktion: Schreibschutz und gewisse Typumwandlungen besitzen besondere Grenzen. Gewünschte Übergänge anhand der lokalen Hilfe und eigenen Testdaten prüfen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine Ganzzahlvariable anlegen

```bash
typeset -i anzahl=2
anzahl=anzahl+3
```

Die zweite Zuweisung speichert wegen `-i` nicht den Text `anzahl+3`, sondern den berechneten Wert 5. Das ist beabsichtigte Arithmetik. Unkontrollierte Eingaben dürfen nicht auf dieselbe Weise übernommen werden.

### Schritt 2: Zwei Namen als Array speichern

```bash
typeset -a namen=("Anna Beispiel" "Ben")
printf 'Anzahl: %s\n' "$anzahl"
printf 'Arrayelemente: %s\n' "${#namen[@]}"
printf 'Erster Name: %s\n' "${namen[0]}"
```

Erwartete Ausgabe:

```text
Anzahl: 5
Arrayelemente: 2
Erster Name: Anna Beispiel
```

Das Leerzeichen im ersten Namen bleibt innerhalb eines Arrayelements. Der Ausdruck `${#namen[@]}` liefert die Elementzahl. Er ist nicht gleichbedeutend mit der Zeichenzahl eines einzelnen Namens.

### Schritt 3: Änderungen einordnen

Die Deklarationen leben in dieser Shell. Sie wurden im Test in einem eigenen Kindprozess erzeugt, nicht in Startdateien geschrieben. Andere Programme erhalten nicht automatisch sämtliche Shellattribute oder Arrays. Exportieren und spätere Interpretation sind gesonderte Themen.

## 6. Typische Anwendungsfälle

### Lokale Hilfsvariablen definieren

Funktionen können eigene Variablen verwenden, ohne bekannte äußere Namen versehentlich zu überschreiben. Bashs Gültigkeitsregeln einschließlich verschachtelter Aufrufe trotzdem berücksichtigen.

### Strukturiert mit Listen arbeiten

Indizierte oder assoziative Arrays machen mehrere Werte beziehungsweise Schlüsselzuordnungen ausdrücklicher als ein einziger unstrukturierter Text. Bei Weitergabe die Elementgrenzen erhalten.

### Konkreten Variablenzustand untersuchen

`typeset -p EIGENER_NAME` zeigt den tatsächlichen Zustand einer bekannten Übungsvariable. Nicht die gesamte Umgebung als allgemeines Diagnosepaket veröffentlichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ganzzahlattribute führen arithmetische Auswertung durch. Quoting schützt nicht allein vor problematischen oder unerwartet erneut interpretierten Werten. Format und Bereich fremder Daten vor solchen Zuweisungen prüfen.

`-r` kann spätere normale Änderungen oder Aufräumen verhindern. `-g` kann äußere Shellzustände verändern, `-n` kann Änderungen auf einen anderen Namen lenken. Exportierte Daten werden an Kindprozesse weitergegeben und können dort sichtbar werden. Deklarationen und mit `-p` ausgegebene Werte deshalb nicht als automatisch unkritische Metadaten betrachten.

## 8. Häufige Fehler

- **Text wird unerwartet gerechnet:** Die Variable besitzt `-i`.
- **Variable fehlt nach Funktionsende:** Sie wurde innerhalb der Funktion lokal angelegt.
- **+r hebt Schreibschutz nicht auf:** Das Attribut ist nicht gewöhnlich reversibel.
- **Arrayelemente gehen verloren:** Ungeeignete oder unzitierte Weitergabe.
- **Verhalten in anderer Shell anders:** Gleicher Name bedeutet nicht identische Implementation.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit neuen eindeutig eigenen Variablennamen in einer separaten Bash beginnen. Nur benötigte Attribute setzen. Vor Schreibschutz oder Namensreferenzen deren langfristige Wirkung verstehen. Keine Systemumgebungsvariablen als Übung zweckentfremden.

**Prüfstand:** Bash 5.2.21, lokale typeset-/declare-Hilfen gelesen. Ganzzahlzuweisung und indiziertes Array in einer Kind-Bash ohne persönliche Startdateien geprüft; drei erwartete Zeilen, Status 0. Keine Benutzerdateien verändert. Schreibschutz, Namensreferenzen, Export, globale Deklaration und andere Shells nicht praktisch geprüft.

## 10. Verwandte Befehle

- `declare`: Synonym in Bash.
- `local`: lokale Variablen in Funktionen.
- `readonly`: Schreibschutz setzen.
- `export`: Werte für Kindprozesse bereitstellen.
- `readarray`: mehrere Eingabezeilen in ein Array lesen.

Ausgangseintrag: Datensatz 95 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
