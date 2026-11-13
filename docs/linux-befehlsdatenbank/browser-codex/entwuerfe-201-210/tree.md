---
id: "tree"
name: "tree"
command: "tree"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "safe"
tags: ["verzeichnisse", "anzeige"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 202
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft"
---

# tree – Verzeichnisstrukturen übersichtlich anzeigen

## 1. Kurzbeschreibung

`tree` zeigt Dateien und Unterordner als eingerückten Baum. Der normale Aufruf liest Verzeichnisinformationen und verändert keine Dateien. **Root ist für zugängliche eigene Verzeichnisse nicht nötig.**

## 2. Was macht der Befehl?

Ohne Pfad wird das aktuelle Verzeichnis angezeigt. Standardmäßig werden versteckte Namen ausgelassen und symbolische Links nicht rekursiv verfolgt. Mit `-l` können verlinkte Verzeichnisbäume zusätzlich durchsucht werden. Die [Debian-Manpage für tree](https://manpages.debian.org/trixie/tree/tree.1.en.html) beschreibt diese Unterschiede.

## 3. Syntax

```bash
tree [OPTIONEN] [VERZEICHNIS ...]
tree -L 2 -- "Projekt"
tree -a -d -- "Projekt"
```

`tree` ist ein separates Programm und nicht auf jeder Minimalinstallation vorhanden.

## 4. Wichtige Optionen

| Option | Bedeutung | Hinweis |
| --- | --- | --- |
| `-L N` | Maximale Darstellungstiefe. | Reduziert Umfang, nicht zwingend sämtliche Metadatenzugriffe. |
| `-a` | Auch versteckte Namen. | Kann sensible Dateinamen zeigen. |
| `-d` | Nur Verzeichnisse. | Keine Dateiliste. |
| `-I MUSTER` | Treffer ausblenden. | Muster zitieren. |
| `-P MUSTER` | Passende Namen anzeigen. | Filterung beeinflusst Zählung. |
| `-l` | Verzeichnis-Symlinks folgen. | Kann Umfang stark vergrößern. |
| `-x` | Auf einem Dateisystem bleiben. | Nicht als Zugriffsschutz verstehen. |
| `-o DATEI` | Ausgabe in Datei schreiben. | **Schreibender Modus**. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Struktur anlegen

```bash
uebung="$(mktemp -d -t netmon-tree-XXXXXX)"
mkdir -p "$uebung/Projekt/docs" "$uebung/Projekt/src"
printf 'Test\n' > "$uebung/Projekt/docs/info.txt"
```

### Schritt 2: Begrenzte Ansicht

```bash
tree -L 2 -- "$uebung/Projekt"
```

Erwartet werden `docs` und `src` als Unterverzeichnisse. `info.txt` liegt eine Ebene tiefer als die Grenze und erscheint in dieser Ansicht nicht.

### Schritt 3: Dateien anzeigen

```bash
tree -L 3 -- "$uebung/Projekt"
```

Nun erscheint auch die Testdatei. Diese Befehle wurden hier **nicht praktisch ausgeführt**.

## 6. Typische Anwendungsfälle

**Projektüberblick:** Kleine Repository-Teilbäume darstellen. **Dokumentation:** Ordneraufbau verständlich zeigen. **Vorabkontrolle:** Mit `-a` versteckte Namen einbeziehen, wenn das ausdrücklich erwünscht ist.

## 7. Risiken, Nebenwirkungen und Vorsicht

Große Bäume können Laufzeit, Ausgabe und Ressourcen beanspruchen. `-a` oder `-f` kann vertrauliche Pfade offenlegen; Terminalprotokolle beachten. `-o` schreibt eine Ausgabedatei, die vorhandene Inhalte ersetzen kann. `-l` folgt Links und kann über den erwarteten Baum hinausführen. Fehlende Leserechte nicht mit `sudo` umgehen.

## 8. Häufige Fehler

| Problem | Ursache | Vorgehen |
| --- | --- | --- |
| `tree: command not found` | Programm fehlt. | Installation nur nach eigener Freigabe; alternativ `find`. |
| Dateien fehlen | `-L`, `-d` oder versteckte Namen. | Optionen überprüfen. |
| Unerwartet viel Ausgabe | Zu tiefe Rekursion oder `-l`. | `-L` setzen, `-l` weglassen. |
| Zugriff verweigert | Verzeichnisrechte. | Auf eigene Pfade beschränken. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst mit `tree -L 2` auf einem eigenen Übungsordner beginnen. Für reine Anzeige weder `-o` noch `-l` verwenden. Bei Veröffentlichung einer Baumansicht Namen auf Geheimnisse prüfen.

**Prüfstand:** Debian-Manpage `tree` 2.2.1 am 2026-11-13 gelesen. Kein lokaler Aufruf und kein Parser-Test. Verhalten auf anderen Versionen sowie Dateisystemgrenzen nicht praktisch geprüft.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `find` | Flexible rekursive Suche. |
| `ls` | Nichtrekursive Verzeichnisliste. |
| `du` | Speicherbelegung messen. |
| `stat` | Metadaten einzelner Pfade. |

**Ausgangseintrag:** `source_record` 202 aus `tools/netmon-linux-befehlsdatenbank-v1.csv` (Zuordnung aus dem übergebenen JSON, Original-CSV hier nicht selbst geprüft). Gegenüber dem Ausgangseintrag wurden die generische Syntax und das `--help`-Platzhalterbeispiel durch konkrete Funktionsweisen, Sicherheitsgrenzen und Quellen ersetzt; die pauschale Risikoeinstufung wurde fachlich neu bewertet. Die ursprünglichen `source`-Felder wurden nicht verändert.
