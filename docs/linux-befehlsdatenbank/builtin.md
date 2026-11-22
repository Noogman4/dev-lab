---
id: "builtin"
name: "builtin"
command: "builtin"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "caution"
tags: ["builtin", "grundlagen & hilfe"]
status: "Builtin-Syntax anhand lokaler Hilfe geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 345
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2; lokale Hilfe gelesen"
---

# builtin – eine Bash-interne Funktion des Interpreters ausdrücklich aufrufen

## 1. Kurzbeschreibung

`builtin` ruft einen eingebauten Bash-Befehl ausdrücklich auf. Es hilft besonders innerhalb einer Shellfunktion, die denselben Namen wie ein Builtin hat. **Root-Rechte sind nicht nötig.** Die Wirkung richtet sich nach dem gewählten Builtin.

## 2. Was macht der Befehl?

Grundlage ist `help builtin` der lokalen Bash. Ein Builtin wird innerhalb des Shellinterpreters implementiert; es benötigt keine gleichnamige ausführbare Datei im Dateisystem.

Eine Funktion namens `cd` könnte beispielsweise zusätzliche eigene Logik enthalten. Ihr Aufruf von `builtin cd` kann dann gezielt zur eingebauten Verzeichniswechselfunktion gelangen, ohne dieselbe Funktion erneut aufzurufen.

Das ist keine Sicherheitsisolation. Ein veränderndes Builtin bleibt verändernd, und bereits von der Shell ausgeführte Argumentexpansionen werden nicht rückgängig gemacht.

## 3. Syntax

```bash
builtin printf '%s\n' 'Hallo NetMon'
builtin pwd
```

Allgemein:

```text
builtin BUILTINNAME [ARGUMENTE]
```

Ein externes Programm wird dadurch nicht zum Builtin. `builtin ls` ist daher kein allgemeiner Weg zum Systemprogramm `ls`.

## 4. Wichtige Optionen

`builtin` braucht keine eigene Optionssammlung. Nach seinem Namen folgen das gewünschte Builtin und dessen Argumente.

| Form | Wirkung | Grenze |
| --- | --- | --- |
| `builtin printf ...` | Bash-intern formatiert ausgeben. | Format und Argumente bleiben relevant. |
| `builtin cd PFAD` | Verzeichnis der aktuellen Shell wechseln. | Reale Zustandsänderung der Shell. |
| `builtin pwd` | Aktuelles Verzeichnis anzeigen. | Kann persönlichen Pfad offenlegen. |
| `builtin NAME` | Das genannte Builtin wählen. | Muss als Builtin verfügbar sein. |

Der Rückgabestatus entspricht grundsätzlich der ausgeführten Aktion; ein unbekannter Builtinname liefert einen Fehler.

## 5. Beispiel erklärt Schritt für Schritt

```bash
(
  netmon_text() {
    builtin printf '%s\n' "$@"
  }
  netmon_text 'Eigene Ausgabe'
)
```

Die Subshell begrenzt die Funktionsdefinition auf die Übung. `"$@"` übergibt jedes Argument getrennt. Das feste Format sorgt dafür, dass die Wörter als Daten behandelt werden.

Die Funktion heißt hier absichtlich anders als ein Standardbefehl. Das veranschaulicht die ausdrückliche Builtinwahl, ohne bestehende Namen der Benutzersitzung umzudefinieren. Der Beispielablauf wurde nicht als separater Lauf geprüft; die Beschreibung beruht auf der lokalen Hilfe.

Für eine echte Wrapperfunktion gleichen Namens verhindert der ausdrückliche Builtinaufruf eine unbeabsichtigte Selbstrekursion. Die übrige Wrapperlogik muss trotzdem korrekt sein.

## 6. Typische Anwendungsfälle

- Ein Builtin innerhalb einer eigenen Wrapperfunktion verwenden.
- Eingebaute und externe Varianten bewusst unterscheiden.
- Eine ungewollte Selbstrekursion vermeiden.
- In Bash-Skripten die gewünschte Interpreterfunktion kenntlich machen.

## 7. Risiken, Nebenwirkungen und Vorsicht

`builtin` entschärft keine Aktion. Ein Aufruf von `builtin exit` kann die betreffende Shell beenden; `builtin cd` verändert das Arbeitsverzeichnis. Ein Funktionswrapper kann darüber hinaus beliebige andere Befehle enthalten.

Die Form ist Bash-spezifisch zu betrachten. Nicht davon ausgehen, dass jede beliebige `/bin/sh` dieselbe Verwaltungsoberfläche bietet.

## 8. Häufige Fehler

- **Externes Programm erwarten:** Es werden nur passende Built-ins gewählt.
- **Argumente als zusammengesetzten Text übergeben:** Die Trennung der Argumente geht verloren.
- **Sicherheitsgarantie annehmen:** Wirkung des gewählten Builtins bleibt bestehen.
- **Wrapper ruft sich selbst auf:** Ausdrückliche Builtinwahl kann erforderlich sein.
- **Andere Shell verwenden:** Unterstützung und Syntax vorher klären.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit reinen Ausgaben wie `printf` üben. Neue Funktionen in einer Subshell halten, wenn keine dauerhafte Sitzungsänderung gewollt ist.

Für die Frage, wie ein Name aufgelöst wird, zuerst `type NAME` verwenden. `builtin` ist ein Ausführungswerkzeug, kein allgemeiner Herkunftsprüfer.

## 10. Verwandte Befehle

- `type`: Art eines Namens anzeigen.
- `command`: Funktionen umgehen oder Befehle abfragen.
- `help`: Builtin-Bedienung lesen.
- `enable`: Built-in-Verfügbarkeit verwalten; verändernde Shellfunktion.

**Prüfstand:** Lokale Bash-Hilfe gelesen. Keine persönliche Wrapperfunktion oder Startdatei geändert.

Ausgangsdatensatz 345 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
