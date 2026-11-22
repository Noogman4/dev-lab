---
id: "kdialog"
name: "kdialog"
command: "kdialog"
category: "Desktop & GUI"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Desktop & GUI", "kdialog"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 262
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; Programm nicht vorhanden"
---

# kdialog – Dialoge in KDE-Shellskripten

## 1. Kurzbeschreibung

kdialog zeigt KDE-/Qt-Dialoge und liefert je nach Dialog eine Antwort über Standardausgabe oder Exitstatus. Es ist kein allgemeiner Systemstatusbefehl. Grafische Sitzung und Dialogtyp bestimmen die benötigten Voraussetzungen.

## 2. Was macht der Befehl?

Die Auswahl eines Dialogtyps ist Teil des Aufrufs. --yesno liefert die Entscheidung über den Status; --inputbox liefert eingegebenen Text. Eine Dateiauswahl gibt zunächst einen Namen zurück und führt nicht automatisch die spätere Dateioperation des Skripts aus. Für Ja/Nein gilt 0 als Ja und 1 als Nein; andere Fehler dürfen nicht als Nein mit erfolgreicher Verarbeitung verwechselt werden.

Quelle, am 2026-11-13 gelesen: [KDE: Shell scripting with KDE dialogs](https://develop.kde.org/docs/administration/kdialog/)

## 3. Syntax

```text
kdialog [ALLGEMEINE-OPTIONEN] DIALOGTYP ARGUMENTE
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--title TEXT` | Fenstertitel festlegen. |
| `--msgbox TEXT` | Informationsdialog anzeigen. |
| `--yesno TEXT` | Entscheidung per Rückgabestatus liefern. |
| `--inputbox TEXT [VORGABE]` | Text abfragen; Standardausgabe und Abbruchstatus auswerten. |
| `--getopenfilename [START] [FILTER]` | Dateinamen auswählen; keine automatische Inhaltsprüfung. |
| `--dontagain GRUPPE:SCHLUESSEL` | Antwortunterdrückung kann Einstellungen speichern; für diese Aufgabe ungeeignet. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen prüfen

Das folgende Muster ist eine Leseübung. Eine funktionierende passende Benutzersitzung und die installierte Implementierung wären Voraussetzungen für die echte Nutzung. Hier werden weder Dialoge noch Benachrichtigungen ausgelöst, Anwendungen gestartet oder Benutzereinstellungen verändert.

### Schritt 2: Muster lesen

**Nicht ausgeführt; keine gemessene Ausgabe:**

```text
kdialog --title "Lernfrage" --yesno "Beispiel verstanden?"
```

Bei Ja wäre Status 0, bei Nein Status 1 zu erwarten. Das Muster löst selbst keine fachliche Folgeaktion aus. Ein Skript müsste den Status direkt sichern oder den Aufruf in einer if-Abfrage behandeln; jeder spätere Befehl überschreibt $?.

### Schritt 3: Ergebnisgrenze verstehen

Ein Exitstatus beschreibt den jeweiligen Werkzeugaufruf. Er beweist keine nachfolgende Benutzeraktion oder erfolgreiche Verarbeitung in einer anderen Anwendung. Sprache, Sitzung und Programmversion können Meldungen und Verhalten verändern.

## 6. Typische Anwendungsfälle

Desktopskripte nachvollziehen: Argumente, Ausgabe und Rückgabestatus vor einer echten Integration getrennt betrachten. Fehler eingrenzen: Erst die dokumentierte Schnittstelle der installierten Variante mit den Anforderungen des Skripts vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Dialoge blockieren Skripte bis zur Antwort und können den realen Desktop unterbrechen. Passwortdialoge verschleiern nur die Anzeige; nachgelagerte Shellvariablen, Protokolle oder Prozessargumente sind dadurch nicht geschützt. Vermerkte Antworten können persistieren. Keine Ausführung mit sudo: Das würde einen anderen Benutzerkontext betreffen und ersetzt keine passende Sitzung.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Kein Fenster | Display-/Qt-Sitzung oder Programm fehlt; keine fremde Sitzung erzwingen. |
| Leere Eingabe | Kann gültiger Text sein; zusätzlich Exitstatus prüfen. |
| Skript läuft nach Abbruch weiter | Dialogausgang wurde nicht vor Folgeaktionen ausgewertet. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zunächst lokale Hilfe und verfügbare Variante prüfen. Benutzereingaben als Daten behandeln, zitieren und vor Weiterverarbeitung validieren. Abbruch und technische Fehler dürfen nicht still als Zustimmung gelten.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; Programm nicht vorhanden. Nicht praktisch geprüft; praktische Prüfung offen. GUI-/Sitzungsintegration, echte Benutzerreaktionen und Änderungen bleiben praktisch offen. Kein Funktionsaufruf ausgeführt. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `zenity` | Andere Dialogschnittstelle mit eigenen Optionen und Statusregeln. |
| `notify-send` | Benachrichtigung statt interaktiver Dialog. |
| `printf` | Terminalausgabe ohne grafische Sitzung. |

Ausgangsdatensatz 262 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
