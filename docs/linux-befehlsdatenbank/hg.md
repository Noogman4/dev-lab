---
id: "hg"
name: "hg"
command: "hg"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "hg"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 279
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; Programm fehlt"
---

# hg – Verteilte Versionsverwaltung mit Mercurial

## 1. Kurzbeschreibung

hg ist die Kommandooberfläche von Mercurial. Ein Repository enthält lokale Changesets; der Arbeitsordner enthält die bearbeitete Fassung. Lesen, Versionswechsel, Aufzeichnen und Übertragen sind verschiedene Unterbefehle mit unterschiedlichen Risiken.

## 2. Was macht der Befehl?

init erzeugt die Verwaltungsdaten .hg. add merkt Dateien für den nächsten Commit vor; es ist kein Git-Index zum Auswählen eines eingefrorenen Inhaltsstands. status und diff zeigen Änderungen im Arbeitsordner. commit zeichnet lokal auf, push überträgt. pull holt Changesets und aktualisiert den Arbeitsordner normalerweise erst mit zusätzlicher Updateanforderung. Benannte Branches sind Bestandteil der Changesetgeschichte; Bookmarks sind bewegliche Markierungen. Beide nicht blind mit Git-Branches gleichsetzen.

Quelle, am 2026-11-13 gelesen: [Mercurial-Befehlshandbuch](https://www.mercurial-scm.org/help/commands), [status](https://www.mercurial-scm.org/help/commands/status) und [pull](https://www.mercurial-scm.org/help/commands/pull)

## 3. Syntax

```text
hg [GLOBALE-OPTIONEN] BEFEHL [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `help BEFEHL`, `version` | Konkrete Schnittstelle und Version lesen. |
| `status` | M geändert, A hinzugefügt, ? unversioniert; weitere Statuszeichen laut Hilfe beachten. |
| `diff` | Arbeitsänderungen als Patch lesen. |
| `log` | Lokale Geschichte betrachten. |
| `--cwd ORDNER`, `-R REPO` | Arbeitsverzeichnis oder Repository ausdrücklich wählen. |
| `update` | Arbeitsfassung wechseln; --clean kann Änderungen verwerfen. |
| `revert` | Arbeitsinhalte zurücksetzen; nicht als automatische Fehlerbehebung verwenden. |
| `-y` | Rückfragen automatisch beantworten; keine Prüfung ersetzen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

**Nicht praktisch ausgeführt; erklärendes Muster.** Die benötigte Umgebung fehlt oder die praktische Ausführung ist gesondert offen.

```bash
uebung="$(mktemp -d -t lernen-279-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
export HGRCPATH=/dev/null
hg init eigen
cd -- eigen || exit 1
printf 'Eigener Text
' > notiz.txt
hg status
hg add notiz.txt
hg status
hg diff

```

### Schritt 3: Ergebnis auswerten

Erwartet wären zuerst ? notiz.txt, danach A notiz.txt und ein Patch mit Eigener Text. Es wird kein Commit angefordert. hg fehlt lokal, daher wurden weder Repository noch Ausgabe des Musters erzeugt. HGRCPATH begrenzt hier das Einlesen üblicher Konfiguration und ist keine Sandbox für fremde Repositories. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Änderungen nachvollziehen: Arbeitsfassung und lokale Geschichte unterscheiden. Zusammenarbeit planen: Holen und Übertragen der Changesets von ihrer Integration trennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Update, Revert und Merge können Arbeitsdateien verändern; Hooks und Erweiterungen können Code ausführen. Remoteoperationen übertragen Daten oder rufen Netzwerke auf. Ungeprüfte Konfiguration nicht aktivieren. Das Beispiel bleibt auf neue eigene Dateien beschränkt. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| abort: no repository found | Arbeitsverzeichnis oder -R prüfen. |
| Changesets da, Dateien unverändert | pull und update unterscheiden. |
| Unbekannte Datei im diff nicht sichtbar | status lesen; unversionierte Dateien sind gesondert markiert. |
| Dateien nach add verändert | Mercurial hat keinen gleichartigen Git-Staginginhalt eingefroren. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `git` | Anderes verteiltes Versionsverwaltungssystem. |
| `diff` | Dateivergleich ohne Geschichte. |
| `hg help config` | Konfigurations- und Erweiterungsgrenzen nachlesen. |

Ausgangsdatensatz 279 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
