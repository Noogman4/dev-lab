---
id: "info"
name: "info"
command: "info"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["info", "grundlagen & hilfe"]
status: "Keine interaktive Benutzersitzung geöffnet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 360
reviewed_at: "2026-11-13"
locally_checked_version: "GNU-Texinfo-Manpage 7.1 gelesen"
---

# info – strukturierte lokale Handbücher lesen

## 1. Kurzbeschreibung

`info` ist ein Leser für Handbücher im Info-Format. Dokumente besitzen Knoten, Menüs und Querverweise. **Root-Rechte sind für das Lesen üblicher installierter Handbücher nicht nötig.**

## 2. Was macht der Befehl?

Die lokale Texinfo-Manpage beschreibt die Suche über die installierten Infoverzeichnisse. Ein Handbuch kann ausführlicher als eine kurze Manpage sein und mehrere verwandte Programme behandeln.

Ein geöffnetes Thema führt den darin beschriebenen Befehl nicht automatisch aus. Die Version der Dokumentation muss trotzdem zur betrachteten Installation passen.

## 3. Syntax

```bash
info
info coreutils
info -f ./eigenes-handbuch.info
```

Ohne Thema erscheint die verfügbare Übersicht. Ein ausdrücklich benanntes eigenes Dokument wird über `-f` gewählt. Seine Herkunft sollte bekannt sein.

## 4. Wichtige Optionen

| Form | Zweck | Grenze |
| --- | --- | --- |
| `-f DATEI` | Bestimmtes Handbuch öffnen. | Kein allgemeiner Textkonverter. |
| `-n KNOTEN` | Knoten wählen. | Name muss im Dokument passen. |
| `--index-search=TEXT` | Indexziel suchen. | Handbuchindex ist keine Internetrecherche. |
| `-k TEXT` | In Handbuchindizes suchen. | Nur vorhandene Dokumentation. |
| `-w` | Dateiposition des Handbuchs zeigen. | Kein Öffnen des beschriebenen Arbeitsprogramms. |
| `-o DATEI` | Ausgewählte Knoten exportieren. | Schreibt eine Datei. |
| `--subnodes` | Unterknoten beim Export einbeziehen. | Ausgabeumfang kann stark wachsen. |

## 5. Beispiel erklärt Schritt für Schritt

```bash
info coreutils
```

Der geplante Aufruf würde das verfügbare Coreutils-Handbuch öffnen. Es wurde hier keine interaktive Leseransicht im Benutzerterminal gestartet. Gelesen wurde die lokale `info`-Manpage.

Innerhalb des Lesers zeigt `H` eine Zusammenfassung der Tastenbelegung. Zum Beenden dient in der üblichen GNU-Ansicht `q`. Bei einer unklaren Navigation zuerst die eingebaute Hilfe lesen.

Fehlt das Thema, bedeutet das nicht automatisch, dass die zugehörigen Programme fehlen. Handbuch und Programm können getrennt paketiert sein.

## 6. Typische Anwendungsfälle

- Ausführlichere GNU-Dokumentation lesen.
- Querverweise zwischen verwandten Themen verfolgen.
- Einen lokalen Index nach einer konkreten Funktion durchsuchen.
- Ausdrücklich ausgewählte Handbuchknoten exportieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Das Lesen ist grundsätzlich beobachtend. Eine Exportoption schreibt dagegen eine Ausgabe, die keine wichtige vorhandene Datei überschreiben soll.

Dokumentation kann Links und auszuführende Beispiele enthalten. Deren Nachvollziehen ist ein eigener Schritt. Einen destruktiven Beispielaufruf nicht allein deshalb übernehmen, weil er in einem Handbuch steht.

## 8. Häufige Fehler

- **Thema nicht gefunden:** Installierte Dokumentation und Suchpfad prüfen.
- **Falscher Knoten:** Handbuchstruktur beachten.
- **`-o` als Anzeigeoption:** Es entsteht eine Datei.
- **Onlineversion gleich lokale Fassung:** Versionsbezug klären.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zunächst Übersicht und Leserhilfe benutzen. Für eine konkrete kurze Programmbedienung kann `man` leichter zugänglich sein.

Nur bekannte eigene Dateien ausdrücklich als Infohandbuch öffnen. Für Arbeitsbefehle aus der Dokumentation zuerst deren tatsächliche Ziele und Folgen klären.

## 10. Verwandte Befehle

- `man`: Handbuchseiten lesen.
- `help`: Bash-Builtin-Dokumentation.
- `apropos`: Manpage-Stichwörter suchen.
- `less`: Allgemeiner Textleser mit anderer Dokumentstruktur.

**Prüfstand:** Lokale Manpage gelesen. Kein Export, keine fremde Info-Datei und keine interaktive Benutzersitzung verändert.

Ausgangsdatensatz 360 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
