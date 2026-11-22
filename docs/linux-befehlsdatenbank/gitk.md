---
id: "gitk"
name: "gitk"
command: "gitk"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "gitk"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 276
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; Programm nicht vorhanden"
---

# gitk – Git-Geschichte grafisch durchsuchen

## 1. Kurzbeschreibung

gitk ist ein grafischer Browser für Git-Repositories. Er stellt Commitgraphen, Commitinformationen und Änderungen dar. Es handelt sich um ein zusätzliches Tcl/Tk-Werkzeug, nicht um einen im Browser geöffneten GitHubdienst.

## 2. Was macht der Befehl?

Der gewählte Revisionsbereich bestimmt die betrachtete Geschichte. Ohne weiteren Bereich steht normalerweise die aktuelle Revision im Mittelpunkt. --all erweitert auf lokale Referenzen einschließlich bereits bekannter Remote-Tracking-Referenzen; es aktualisiert sie nicht aus dem Netzwerk. Pfadfilter können die dargestellte Geschichte vereinfachen. Ein nicht angezeigter Commit ist daher nicht automatisch verloren. Eine Historienansicht ersetzt keinen Vergleich aktueller uncommitteter Änderungen.

Quelle, am 2026-11-13 gelesen: [Git-Projekthandbuch: gitk](https://git-scm.com/docs/gitk)

## 3. Syntax

```text
gitk [OPTIONEN] [REVISIONSBEREICH] [--] [PFAD...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--all` | Alle vorhandenen Referenzen betrachten; kein fetch. |
| `--since=DATUM`, `--until=DATUM` | Zeitbereich filtern; Zeitzone beachten. |
| `--branches`, `--tags`, `--remotes` | Referenzgruppen auswählen. |
| `--full-history` | Bei Pfadfiltern weniger Geschichte wegvereinfachen. |
| `A..B` | Von B erreichbare, von A nicht erreichbare Commits. |
| `-- PFAD` | Revisionen von Pfadargumenten trennen; Namen zitieren. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen prüfen

Das folgende Muster ist eine Leseübung. Eine funktionierende passende Benutzersitzung und die installierte Implementierung wären Voraussetzungen für die echte Nutzung. Hier werden weder Dialoge noch Benachrichtigungen ausgelöst, Anwendungen gestartet oder Benutzereinstellungen verändert.

### Schritt 2: Muster lesen

**Nicht ausgeführt; keine gemessene Ausgabe:**

```text
gitk --all -- docs/eigene-notiz.md
```

Das Muster setzt ein bereits existierendes vertrauenswürdiges Repository mit Geschichte voraus; es wird hier keines für einen Demo-Commit angelegt. Die Ansicht würde auf den angegebenen Pfad eingegrenzt. Lokale Remote-Referenzen sind nur der zuletzt gespeicherte Stand, kein Nachweis eines aktuellen Servers.

### Schritt 3: Ergebnisgrenze verstehen

Ein Exitstatus beschreibt den jeweiligen Werkzeugaufruf. Er beweist keine nachfolgende Benutzeraktion oder erfolgreiche Verarbeitung in einer anderen Anwendung. Sprache, Sitzung und Programmversion können Meldungen und Verhalten verändern.

## 6. Typische Anwendungsfälle

Desktopskripte nachvollziehen: Argumente, Ausgabe und Rückgabestatus vor einer echten Integration getrennt betrachten. Fehler eingrenzen: Erst die dokumentierte Schnittstelle der installierten Variante mit den Anforderungen des Skripts vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

GUI-Aktionen und Kontextmenüs dürfen nicht pauschal als lesend gelten. Externe Editoren oder weitere Git-Aktionen können gestartet werden; Einstellungen können gespeichert werden. Fremde Repositorykonfiguration und Hilfsprogramme sind Vertrauensgrenzen. Kein Commit, Reset, Checkout oder Netzwerkaufruf gehört zu dieser Leseübung. Keine Ausführung mit sudo: Das würde einen anderen Benutzerkontext betreffen und ersetzt keine passende Sitzung.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| gitk fehlt trotz git | Kann als separates Paket verteilt sein; hier fehlt es. |
| Kein Display | Tcl/Tk benötigt eine grafische Sitzung. |
| Dateiname als Revision verstanden | -- vor Pfaden einsetzen. |
| Commit fehlt in Ansicht | Filter und erreichbare Referenzen prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zunächst lokale Hilfe und verfügbare Variante prüfen. Benutzereingaben als Daten behandeln, zitieren und vor Weiterverarbeitung validieren. Abbruch und technische Fehler dürfen nicht still als Zustimmung gelten.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; Programm nicht vorhanden. Nicht praktisch geprüft; praktische Prüfung offen. GUI-/Sitzungsintegration, echte Benutzerreaktionen und Änderungen bleiben praktisch offen. Kein Funktionsaufruf ausgeführt. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `git log --graph` | Terminalansicht der Geschichte. |
| `git diff` | Änderungen gezielt vergleichen. |
| `git show` | Einzelnen Commit oder Objektinhalt lesen. |

Ausgangsdatensatz 276 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
