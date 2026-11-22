---
id: "man"
name: "man"
command: "man"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["man", "grundlagen & hilfe"]
status: "Keine fremde Dokumentdatei oder interaktive Benutzersitzung geöffnet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 362
reviewed_at: "2026-11-13"
locally_checked_version: "man-db 2.12.0; lokale Manpage gelesen"
---

# man – installierte Handbuchseiten gezielt lesen

## 1. Kurzbeschreibung

`man` zeigt Handbuchseiten zu Programmen, Funktionen und Systemthemen. **Root-Rechte sind für das normale Lesen nicht nötig.** Das beschriebene Programm wird nicht als Arbeitsaktion gestartet.

## 2. Was macht der Befehl?

Die lokale man-db-Manpage erklärt die Suche nach Name und Abschnitt. Derselbe Name kann eine Benutzeranwendung, einen Systemaufruf oder ein Dateiformat bezeichnen.

Wichtige Abschnitte sind beispielsweise 1 für Benutzerbefehle, 3 für Bibliotheksfunktionen, 5 für Dateiformate und 8 für Systemverwaltung. Eine Seite aus Abschnitt 8 ist trotzdem ohne administrative Ausführung lesbar.

## 3. Syntax

```bash
man ls
man 1 printf
man 3 printf
```

Die zwei `printf`-Seiten behandeln verschiedene Gegenstände. Für das Bash-Builtin ist zusätzlich `help printf` relevant. Name und Abschnitt müssen zur Frage passen.

## 4. Wichtige Optionen

| Form | Zweck | Grenze |
| --- | --- | --- |
| `man ABSCHNITT NAME` | Bestimmte Seite wählen. | Vermeidet gleichnamige andere Themen. |
| `-k SUCHWORT` | Kurzbeschreibungen durchsuchen. | Entspricht der Aufgabe von `apropos`. |
| `-f NAME` | Kurzbeschreibung zeigen. | Entspricht der Aufgabe von `whatis`. |
| `-w NAME` | Fundort anzeigen. | Keine Ausführung des Programms. |
| `-a NAME` | Mehrere passende Seiten lesen. | Umfang wächst. |
| `-l DATEI` | Eine lokale Manpage verarbeiten. | Nur bekannte geeignete Dokumente verwenden. |

Die tatsächliche Navigation hängt auch vom gewählten Pager ab. In einer üblichen `less`-Ansicht beendet `q` das Lesen.

## 5. Beispiel erklärt Schritt für Schritt

```bash
man 1 printf
```

Zuerst wird Abschnitt 1 festgelegt, dann der Name. Im Handbuch zunächst NAME und SYNOPSIS lesen. Danach die benötigte Option und Hinweise zur Ausgabe betrachten.

Notation wie `[OPTION]` ist eine Beschreibung optionaler Argumente, keine wörtlich zu kopierende Zeichenfolge. Ein senkrechter Alternativstrich in einer Syntaxzeile bedeutet eine Auswahl.

Die Seite wurde für diesen Eintrag nicht im Benutzerterminal geöffnet. Die Beschreibung beruht auf der gelesenen lokalen `man`-Manpage.

## 6. Typische Anwendungsfälle

- Optionen vor einem Arbeitsaufruf verstehen.
- Gleichnamige Programme und Bibliotheksfunktionen unterscheiden.
- Dateiformate oder Konfigurationen nachlesen.
- Eine konkrete lokale Fassung gegenüber einem Onlinebeispiel einordnen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Normales Lesen installierter Seiten verändert keine Arbeitsdaten. Ein Pager kann jedoch eigene Funktionen besitzen; unbekannte Tastenkombinationen nicht als reine Navigation voraussetzen.

Fremde lokale Handbuchdateien werden formatiert und verarbeitet. Ihre Herkunft deshalb berücksichtigen. Ein Handbuchinhalt oder enthaltenes Beispiel ist keine automatische Freigabe zur beschriebenen Änderung.

## 8. Häufige Fehler

- **Falscher Abschnitt:** Thema gezielt auswählen.
- **Seite fehlt, Programm fehlt:** Dokumentation kann getrennt installiert sein.
- **Syntaxnotation kopieren:** Erst in konkrete Argumente übersetzen.
- **Root für Abschnitt 8:** Lesen erfordert keine Verwaltungsrechte.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit bekannten installierten Seiten beginnen. Für eine reine Namenssuche `apropos`, für Bash-Built-ins die lokale `help`-Funktion nutzen.

Vor Lösch- oder Verwaltungsbefehlen außerdem Ziel und Umfang prüfen. Die Existenz einer dokumentierten Option macht ihre Anwendung im konkreten Fall nicht richtig.

## 10. Verwandte Befehle

- `apropos`: Stichwortsuche.
- `whatis`: Kurze Namensbeschreibung.
- `info`: Strukturierte Handbücher.
- `help`: Bash-Builtin-Dokumentation.

**Prüfstand:** Lokale Manpage gelesen. Kein Index neu aufgebaut und keine fremde Formatdatei verarbeitet.

Ausgangsdatensatz 362 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
