---
id: "alias"
name: "alias"
command: "alias"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "caution"
tags: ["alias", "grundlagen & hilfe"]
status: "Lokale Hilfe geprüft; Beispiel ohne dauerhafte Shellkonfiguration"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 343
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2; lokale Builtin-Hilfe gelesen"
---

# alias – Abkürzungen in Bash definieren und anzeigen

## 1. Kurzbeschreibung

`alias` ist ein Shell-Builtin, das Abkürzungen definiert oder zeigt. In Bash wird ein passendes Befehlswort durch vorbereiteten Text ersetzt. **Root-Rechte sind nicht nötig.** Die Definition gilt zunächst nur in der betreffenden Shell.

## 2. Was macht der Befehl?

Ein Alias spart Tipparbeit, ist aber kein eigenständiges Programm. Nach der Ersetzung verarbeitet die Shell den entstandenen Aufruf mit dessen tatsächlicher Wirkung.

Grundlage ist die lokale Bash-Hilfe `help alias`. Die [GNU-Beschreibung von Aliasen](https://www.gnu.org/s/bash/manual/html_node/Aliases.html) bestätigt insbesondere die Bedeutung des Einlesezeitpunkts; die Onlinevollseite war nicht erreichbar. Für Versionsdetails gilt die lokale Hilfe.

Für komplexe Logik und Parameter ist eine Funktion meist geeigneter. Ein Alias erhält keine eigene Argumentverarbeitung wie ein Skript mit eigenen Positionsparametern.

## 3. Syntax

```bash
alias netmon_liste='ls -l'
alias netmon_liste
alias -p
```

Keine Leerzeichen um das Gleichheitszeichen setzen. Die einfachen Anführungszeichen halten den vorgesehenen Text bei der Definition zusammen.

## 4. Wichtige Optionen

| Form | Aufgabe | Ergebnis |
| --- | --- | --- |
| `alias NAME='TEXT'` | Definition setzen. | Ändert die aktuelle Aliasliste. |
| `alias NAME` | Eine Definition zeigen. | Führt den Aliasinhalt nicht aus. |
| `alias -p` | Definitionen darstellen. | Kann persönliche Abkürzungen offenlegen. |
| `alias` | Aliasliste anzeigen. | Nicht automatisch dauerhafte Konfiguration. |

Bash-Aliasexpansion ist in nicht interaktiven Shells normalerweise nicht eingeschaltet. Skripte deshalb nicht von den persönlichen interaktiven Aliasen abhängig machen.

## 5. Beispiel erklärt Schritt für Schritt

```bash
(
  alias netmon_liste='ls -l'
  alias netmon_liste
)
```

Die Klammern erzeugen eine Subshell. Darin wird eine neue Abkürzung definiert und anschließend ihre Definition angezeigt. Es wird bewusst nicht innerhalb desselben bereits eingelesenen Blocks auf ihre Expansion vertraut.

Nach Ende der Subshell verändert diese Definition die aufrufende Shell nicht. Das Beispiel ist anhand der lokalen Hilfe beschrieben; es wurde keine persönliche Startdatei verändert und kein Verzeichnis über den Alias aufgelistet.

In einer interaktiven Bash könnte die Definition in einer eigenen Eingabezeile stehen. Erst eine nachfolgend neu eingelesene Zeile würde den Namen als Alias verwenden. Definition und Nutzung auf derselben Zeile sind eine häufige Fehlerquelle.

## 6. Typische Anwendungsfälle

- Persönliche kurze Namen für oft verwendete Aufrufe.
- Anzeige einer vorhandenen Abkürzung vor ihrer Nutzung.
- Fehlersuche, wenn ein Name unerwartete Zusatzoptionen verwendet.
- Kleine vorübergehende Bedienhilfen in einer interaktiven Sitzung.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein Alias kann unter einem vertrauten Namen einen anderen Aufruf starten. Namen wie `rm` deshalb nicht allein anhand des getippten Wortes bewerten. Die tatsächliche Definition ist entscheidend.

Anführungszeichen und Zeitpunkt der Expansion beeinflussen, wann Variablen ausgewertet werden. Fremde Aliasdateien nicht ungeprüft mit `source` laden; ihr übriger Inhalt könnte ebenfalls Befehle ausführen.

## 8. Häufige Fehler

- **Leerzeichen bei `NAME = TEXT`:** Falsche Syntax.
- **Alias im Skript fehlt:** Nicht interaktive Expansion beachten.
- **Definition und Nutzung in einem Block:** Bash hat diesen bereits eingelesen.
- **`$1` wie bei einer Funktion benutzen:** Alias hat keine eigene Parameterliste.
- **Neue Shell kennt Alias nicht:** Es war nur eine Sitzungsdefinition.

## 9. Sichere Varianten oder Tipps für Einsteiger

Eigene eindeutige Namen wählen und zunächst nur die Definition anzeigen. Dauerhafte Einträge in Startdateien erst nach bewusster Entscheidung ergänzen.

Mit `type NAME` lässt sich prüfen, wie Bash einen Namen versteht. Mit `unalias NAME` wird die entsprechende Abkürzung aus der aktuellen Aliasliste entfernt.

## 10. Verwandte Befehle

- `unalias`: Aliasdefinition entfernen.
- `type`: Auflösung eines Namens betrachten.
- `command`: Funktionen bei einem Aufruf umgehen beziehungsweise Namen abfragen.
- `help`: Lokale Builtin-Dokumentation lesen.

**Prüfstand:** Lokale Bash-Hilfe gelesen. Keine dauerhafte Aliasdefinition oder persönliche Shellkonfiguration geändert.

Ausgangsdatensatz 343 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
