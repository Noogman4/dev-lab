---
id: "zenity"
name: "zenity"
command: "zenity"
category: "Desktop & GUI"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Desktop & GUI", "zenity"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 267
reviewed_at: "2026-11-13"
locally_checked_version: "zenity 4.0.1"
---

# zenity – GTK-Dialoge und deren Antworten auswerten

## 1. Kurzbeschreibung

zenity zeigt GTK-Dialoge für Shellskripte. Antworten kommen abhängig vom Dialogtyp über Standardausgabe oder Exitstatus zurück. Der Aufruf benötigt bei echter Dialognutzung eine passende grafische Sitzung.

## 2. Was macht der Befehl?

--question stellt eine Entscheidungsfrage, --entry liefert Text, --file-selection einen ausgewählten Namen. Diese Daten sind noch keine validierte fachliche Eingabe. Ein Dateiauswahldialog führt nicht automatisch die vom Skript danach gewünschte Dateioperation aus. Die dokumentierte Frageantwort unterscheidet 0 für Bestätigung, 1 für Abbruch und 5 für Zeitüberschreitung. Andere Fehler dürfen nicht als Zustimmung behandelt werden.

Quelle, am 2026-11-13 gelesen: [Zenity-Projekthandbuch als Debian-Manpage](https://manpages.debian.org/trixie/zenity/zenity.1.en.html) und lokale Manpage; die früheren GNOME-help-URLs waren nicht erreichbar und sind kein verwendeter Inhaltsbeleg

## 3. Syntax

```text
zenity DIALOGTYP [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--question`, `--entry`, `--info` | Dialogtyp ausdrücklich wählen. |
| `--title=TEXT`, `--text=TEXT` | Fensterüberschrift und Inhalt setzen. |
| `--timeout=SEKUNDEN` | Dialog nach Zeit beenden; Status 5 ist keine Bestätigung. |
| `--default-cancel` | Bei Fragen Abbruch voreinstellen. |
| `--no-markup` | Text bei unterstützten Dialogtypen ohne Pango-Markup behandeln. |
| `--file-selection --save` | Dateinamen auswählen; Anwendung muss Schreiben selbst verantworten. |
| `--progress --auto-kill` | Kann den Elternprozess bei Abbruch beenden; kein harmloses Darstellungsdetail. |
| `--help-all`, `--version` | Optionen und tatsächlich installierte Version lesen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen prüfen

Das folgende Muster ist eine Leseübung. Eine funktionierende passende Benutzersitzung und die installierte Implementierung wären Voraussetzungen für die echte Nutzung. Hier werden weder Dialoge noch Benachrichtigungen ausgelöst, Anwendungen gestartet oder Benutzereinstellungen verändert.

### Schritt 2: Muster lesen

**Nicht ausgeführt; keine gemessene Ausgabe:**

```text
zenity --question --default-cancel --timeout=15 --title="Lernfrage" --text="Beispiel verstanden?"
```

Das Muster würde bis zu 15 Sekunden auf eine Antwort warten. Nur Bestätigung mit Status 0 dürfte ein Skript als Zustimmung werten; 1 und 5 sind getrennt zu behandeln. Hier wurde kein Dialog angezeigt. Ein technischer Displayfehler wäre ebenfalls keine Benutzerantwort.

### Schritt 3: Ergebnisgrenze verstehen

Ein Exitstatus beschreibt den jeweiligen Werkzeugaufruf. Er beweist keine nachfolgende Benutzeraktion oder erfolgreiche Verarbeitung in einer anderen Anwendung. Sprache, Sitzung und Programmversion können Meldungen und Verhalten verändern.

## 6. Typische Anwendungsfälle

Desktopskripte nachvollziehen: Argumente, Ausgabe und Rückgabestatus vor einer echten Integration getrennt betrachten. Fehler eingrenzen: Erst die dokumentierte Schnittstelle der installierten Variante mit den Anforderungen des Skripts vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Dialoge unterbrechen den echten Desktop und können blockieren. Eingaben und ausgewählte Dateinamen dürfen nicht per eval ausgeführt werden. Versteckte Passworteingabe schützt keine späteren Logs. Bei --progress ist --auto-kill ein Eingriff in den Elternprozess und wird hier nicht getestet. Keine Ausführung mit sudo: Das würde einen anderen Benutzerkontext betreffen und ersetzt keine passende Sitzung.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Cannot open display | Grafische Sitzung fehlt; keine fremde Displayberechtigung setzen. |
| Ausgabe leer | Status und Dialogtyp prüfen; leere Eingabe kann gültig sein. |
| Timeout behandelt wie Ja | Status 5 gesondert auswerten. |
| Option ignoriert | Lokale Version beachten: etwa --attach ist in der gelesenen Manpage veraltet und wirkungslos. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zunächst lokale Hilfe und verfügbare Variante prüfen. Benutzereingaben als Daten behandeln, zitieren und vor Weiterverarbeitung validieren. Abbruch und technische Fehler dürfen nicht still als Zustimmung gelten.

**Prüfstand am 2026-11-13:** zenity 4.0.1. Praktisch geprüft: GUI-/Sitzungsintegration, echte Benutzerreaktionen und Änderungen bleiben praktisch offen. Nur die Hilfe/Version wurde lokal aufgerufen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `kdialog` | KDE-Dialoge mit anderer Schnittstelle. |
| `notify-send` | Passive Meldungen statt Antwortdialog. |
| `read` | Eingabe in einer Terminal-Shell. |

Ausgangsdatensatz 267 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
