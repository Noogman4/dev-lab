---
id: "git"
name: "git"
command: "git"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "git"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 275
reviewed_at: "2026-11-13"
locally_checked_version: "git 2.43.0"
---

# git – Versionen und Änderungen mit Git unterscheiden

## 1. Kurzbeschreibung

Git verwaltet lokale Versionsgeschichte und kann sie mit anderen Repositories austauschen. Sein Verhalten hängt vollständig vom Unterbefehl ab: diff ist eine Ansicht, commit schreibt Geschichte und push überträgt sie. Git ist nicht pauschal lesend.

## 2. Was macht der Befehl?

Arbeitsbaum, Index und Commit sind verschiedene Zustände. add übernimmt einen aktuellen Dateiinhalt in den Index; spätere Arbeitsbaumänderungen bleiben davon getrennt. diff vergleicht gewöhnlich Arbeitsbaum gegen Index, diff --cached Index gegen Commit. commit allein veröffentlicht nichts, push ist ein gesonderter Netzwerkschritt. fetch aktualisiert entfernte Referenzen; pull kann zusätzlich integrieren. Das Beispiel braucht bewusst weder Repository noch Index, Commit oder Remote.

Quelle, am 2026-11-13 gelesen: [Git-Handbuch](https://git-scm.com/docs/git), [git-diff](https://git-scm.com/docs/git-diff)

## 3. Syntax

```text
git [GLOBALE-OPTIONEN] UNTERBEFEHL [ARGUMENTE]
git diff --no-index [OPTIONEN] PFAD-ALT PFAD-NEU
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `status --short` | Arbeitsbaum-/Indexstatus knapp anzeigen; unversionierte Dateien gesondert erkennen. |
| `diff`, `diff --cached` | Nicht vorgemerkte beziehungsweise vorgemerkte Änderungen vergleichen. |
| `diff --no-index` | Zwei Pfade ohne Repository vergleichen; Unterschiede ergeben Status 1. |
| `--no-pager` | Pager für den Aufruf abschalten. |
| `--no-ext-diff --no-textconv` | Externe Diff-/Textkonverter für den Vergleich ausschließen. |
| `-C ORDNER` | Unterbefehl in einem bestimmten Verzeichnis ausführen. |
| `restore`, `reset --hard`, `clean` | Können Inhalte verwerfen; keine Anfänger-Reparatur ohne genaue Zielklärung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

Das folgende Beispiel wurde ausgeführt.

```bash
uebung="$(mktemp -d -t lernen-275-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
git --version
printf 'Version eins
' > vorher.txt
printf 'Version zwei
' > nachher.txt
if git --no-pager diff --no-index --no-ext-diff --no-textconv -- vorher.txt nachher.txt; then
  status=0
else
  status=$?
fi
test "$status" -eq 1
printf 'Unterschiede erkannt, Status %s
' "$status"

```

### Schritt 3: Ergebnis auswerten

Der Patch zeigt eine entfernte Zeile Version eins und eine hinzugefügte Zeile Version zwei. Status 1 ist bei diesem Diff der erwartete Unterschied, kein technischer Fehler. Nur eigene Dateien wurden verglichen; es wurde kein Repository angelegt und weder etwas vorgemerkt noch committet oder übertragen. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Änderungen prüfen: Vor jedem freigegebenen Commit genau den vorgesehenen Diff lesen. Versionsgeschichte verstehen: Lokale Referenzen, Arbeitsstand und Remotezustand auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Git kann löschen, überschreiben, Historie umschreiben und Daten veröffentlichen. Hooks, Filter, Helfer und Unterprojekte sind Vertrauensgrenzen. Keine Geheimnisse in einen Index übernehmen; nach Veröffentlichung reicht bloßes Löschen aus der letzten Datei nicht. Das Beispiel benutzt keine Netzanfragen. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Leerer diff trotz geändertem Inhalt | Vielleicht bereits vorgemerkt; diff --cached und status unterscheiden. |
| Untracked fehlt im normalen diff | Git kennt die Datei noch nicht; status zeigt sie. |
| Status 1 bei no-index | Unterschiede sind erwartet; andere Fehler getrennt behandeln. |
| Detached HEAD | Kein Anlass für Reset; Referenzen und Arbeitsstand zuerst lesen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** git 2.43.0. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gitk` | Grafische Ansicht von Git-Geschichte. |
| `diff` | Dateivergleich ohne Versionsverwaltung. |
| `hg` | Anderes verteiltes Versionsverwaltungssystem. |

Ausgangsdatensatz 275 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
