---
id: "function"
name: "function"
command: "function"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "caution"
tags: ["bash builtins", "function"]
status: "Lokale Primärhilfe und Parameter-/Standardwertbeispiel praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 86
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# function – Wiederverwendbare Bash-Funktionen definieren

## 1. Kurzbeschreibung

`function` ist ein Bash-Schlüsselwort zum Definieren einer Shellfunktion. Eine Funktion fasst Befehle unter einem Namen zusammen und kann Argumente erhalten. **Root-Rechte sind dafür nicht nötig.** Die Definition allein führt den Körper noch nicht als normalen Funktionsaufruf aus.

Die Funktion wird erst durch ihren Namen aufgerufen. Ihre späteren Aktionen haben die Rechte der ausführenden Shell und können entsprechend Daten lesen oder verändern.

## 2. Was macht der Befehl?

Bash speichert den Funktionskörper und führt ihn bei einem Aufruf im Kontext der aufrufenden Shell aus. Es entsteht dabei nicht automatisch ein vollständig isolierter Prozess. Änderungen am Arbeitsverzeichnis oder an nichtlokalen Variablen können deshalb nach dem Aufruf fortbestehen.

Argumente sind im Körper als `$1`, `$2` und insgesamt als `"$@"` verfügbar. Der Status einer Funktion ist gewöhnlich der Status ihres letzten ausgeführten Befehls oder ein ausdrücklich mit `return` gesetzter Wert. Textausgabe und Rückgabestatus sind getrennte Kanäle. Primärquelle ist die lokal gelesene Hilfe `help function` aus Bash 5.2.21; weiterführend: [Bash-Funktionen](https://www.gnu.org/software/bash/manual/html_node/Shell-Functions.html).

## 3. Syntax

```text
function NAME {
  BEFEHLE
}

NAME() {
  BEFEHLE
}
```

Die zweite Form benötigt das Wort `function` nicht und ist in vielen anderen Shells gebräuchlicher. Die konkrete Unterstützung von Bash-Erweiterungen im Körper bleibt trotzdem shellabhängig. Geschweifte Klammern sind eigene Grammatikzeichen; Trennzeichen und Zeilenumbrüche müssen stimmen.

## 4. Wichtige Optionen

`function` besitzt keine gewöhnlichen Schalter. Nützliche zugehörige Elemente sind:

| Element | Bedeutung | Hinweis |
| --- | --- | --- |
| `NAME ARGUMENT ...` | Definierte Funktion aufrufen. | Kein zusätzliches function-Schlüsselwort nötig. |
| `local name=...` | Variable im Funktionsbereich anlegen. | Bash-Mechanismus, nicht beliebig außerhalb verwenden. |
| `"$@"` | Argumente einzeln weiterreichen. | Grenzen einschließlich Leerzeichen erhalten. |
| `return STATUS` | Funktion mit Status verlassen. | Gibt keinen beliebig langen Textwert zurück. |
| `declare -f NAME` | Definition anzeigen. | Kann vertrauliche fest eingetragene Werte offenlegen. |
| `unset -f NAME` | Funktionsdefinition entfernen. | Nicht mit einer gleichnamigen Variablen verwechseln. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine reine Ausgabefunktion definieren

In einer eigenen Bash-Sitzung:

```bash
function begruesse {
  local name="${1:-Gast}"
  printf 'Hallo %s\n' "$name"
}
begruesse "Anna Beispiel"
begruesse
```

### Schritt 2: Parameter und Standardwert verstehen

Beim ersten Aufruf erhält `$1` den gesamten Text `Anna Beispiel`. Die Anführungszeichen im Aufruf bewahren das Leerzeichen. `local` hält die eigene Variable im Funktionsbereich. `${1:-Gast}` setzt bei fehlendem oder leerem ersten Wert den Standard `Gast` ein.

Beim zweiten Aufruf fehlt ein Argument. Die Funktion verwendet deshalb ihren Standard. Es wird keine Benutzerdatei gelesen und kein Konto abgefragt.

### Schritt 3: Ausgabe vergleichen

```text
Hallo Anna Beispiel
Hallo Gast
```

Die beiden sichtbaren Zeilen stammen von den zwei Aufrufen, nicht vom bloßen Definieren. Das Beispiel demonstriert keine Trennung von Rechten und keine dauerhafte Installation einer Funktion.

## 6. Typische Anwendungsfälle

### Wiederholte Arbeit bündeln

Eine gut benannte Funktion vermeidet mehrfach kopierte Befehlsfolgen. Sie sollte klar dokumentieren, welche Argumente sie erwartet, was sie ausgibt und welche Nebenwirkungen entstehen.

### Fehlerbehandlung vereinheitlichen

Eine eigene Hilfsfunktion kann Meldungen und Statuswerte konsistent erzeugen. Dabei den ursprünglichen Fehlerstatus sichern, bevor andere Befehle ihn überschreiben.

### Kleine Skripte lesbarer machen

Funktionen können sinnvolle fachliche Schritte benennen. Zu große oder versteckt zustandsverändernde Funktionen erschweren das Verständnis dagegen; globale Variablen und Verzeichniswechsel sparsam verwenden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Eine Funktion kann einen bekannten Befehlsnamen überdecken. Dann kann ein scheinbar gewöhnlicher Aufruf etwas anderes tun als erwartet. `type NAME` hilft bei der Einordnung, ist aber keine vollständige Sicherheitsprüfung.

Der Körper kann Dateien löschen, Programme starten oder Verbindungen herstellen. `function` ist keine Sandbox. Fremde Definitionen nicht ungeprüft per `source` laden. Ungeprüfte Argumente nicht mit `eval` ausführen; sie als Daten behandeln und korrekt zitieren. Rekursion benötigt eine begrenzte Abbruchbedingung, damit nicht unkontrolliert Ressourcen verbraucht werden.

## 8. Häufige Fehler

- **Nach Definition keine Ausgabe:** Ein Aufruf fehlt; die Definition ist keine unmittelbare Wiederholung.
- **Variable bleibt unerwartet verändert:** Ohne lokale Begrenzung wurde Shellzustand verändert.
- **Text mit return übergeben:** `return` erwartet einen Status, nicht den gewünschten Ausgabetext.
- **Argument mit Leerzeichen zerfällt:** Quoting bei Aufruf oder Weitergabe fehlt.
- **Unter anderer Shell Fehler:** Bash-Schlüsselwort oder Körpererweiterung wird dort nicht unterstützt.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer reinen Ausgabe und klaren Parametern beginnen. Funktionsnamen wählen, die bekannte Systembefehle nicht verdecken. In Beispielen einen eigenen Bereich oder eine separate Bash verwenden; dauerhafte Aufnahme in Startdateien ist ein zusätzlicher Schritt.

**Prüfstand:** Bash 5.2.21 und lokale Funktionshilfe geprüft. Definition und beide Aufrufe in einer getrennten Bash ohne persönliche Startdateien ausgeführt; erwartete zwei Zeilen, Status 0. Keine Startdateien oder Benutzerdateien verändert. Rekursion, exportierte Funktionen und Fehlerpfade nicht praktisch geprüft.

## 10. Verwandte Befehle

- `local`, `declare`: Variablen und Attribute verwalten.
- `return`: Funktion vorzeitig mit Status verlassen.
- `type`, `declare -f`: Definition und Auflösungsart untersuchen.
- `source`: Code in die aktuelle Shell einlesen; eigene Risiken beachten.

Ausgangseintrag: Datensatz 86 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
