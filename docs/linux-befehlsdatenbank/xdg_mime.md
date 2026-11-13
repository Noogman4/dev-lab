---
id: "xdg_mime"
name: "xdg-mime"
command: "xdg-mime"
category: "Desktop & GUI"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Desktop & GUI", "xdg-mime"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 264
reviewed_at: "2026-11-13"
locally_checked_version: "xdg-mime 1.1.3"
---

# xdg-mime – MIME-Typen und Standardanwendungen unterscheiden

## 1. Kurzbeschreibung

xdg-mime kann Dateitypen und Standards abfragen, aber auch Zuordnungen ändern und Typbeschreibungen installieren. Abfrage, Standardhandler und MIME-Datenbank sind getrennte Aufgaben. Die pauschale Einstufung als lesend greift deshalb zu kurz.

## 2. Was macht der Befehl?

query filetype untersucht eine Datei und liefert einen MIME-Typ. query default sucht zu einem schon bekannten Typ die Desktop-Dateikennung der Standardanwendung. Ein Dateiname mit passender Endung garantiert weder einen bestimmten Inhalt noch dessen Sicherheit. default fordert eine neue Zuordnung an; install verarbeitet dagegen eine XML-Typbeschreibung und ist keine Programminstallation.

Quelle, am 2026-11-13 gelesen: [xdg-utils: xdg-mime](https://portland.freedesktop.org/doc/xdg-mime.html) und lokale Manpage

## 3. Syntax

```text
xdg-mime query filetype DATEI
xdg-mime query default MIME-TYP
xdg-mime default ANWENDUNG.desktop MIME-TYP...
xdg-mime install [--mode user|system] XML-DATEI
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `query filetype` | Erkannten MIME-Typ lesen. |
| `query default` | Standardhandler lesen; leere Antwort ist keine Programmprüfung. |
| `default` | Voreinstellung ändern; Anwendung muss passend registriert sein. |
| `install`, `uninstall` | Typbeschreibungen hinzufügen/entfernen; verändert Datenbanken. |
| `--mode user/system` | Geltungsbereich für (De-)Installation; Root verwendet standardmäßig system. |
| `--novendor` | Namenskonfliktschutz abschalten, nicht nötig für eine Abfrage. |
| `--version` | xdg-utils-Version ausgeben. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen prüfen

Das folgende Muster ist eine Leseübung. Eine funktionierende passende Benutzersitzung und die installierte Implementierung wären Voraussetzungen für die echte Nutzung. Hier werden weder Dialoge noch Benachrichtigungen ausgelöst, Anwendungen gestartet oder Benutzereinstellungen verändert.

### Schritt 2: Muster lesen

**Nicht ausgeführt; keine gemessene Ausgabe:**

```text
xdg-mime query filetype ./eigene-notiz.txt
xdg-mime query default text/plain
```

Der erste Aufruf setzt eine zuvor selbst erzeugte, existierende Datei voraus und würde beispielsweise text/plain liefern; das ist hier keine Messung. Der zweite fragt nur eine Zuordnung ab und öffnet nichts. Eine leere Antwort muss zusammen mit Status und Desktopkontext untersucht werden.

### Schritt 3: Ergebnisgrenze verstehen

Ein Exitstatus beschreibt den jeweiligen Werkzeugaufruf. Er beweist keine nachfolgende Benutzeraktion oder erfolgreiche Verarbeitung in einer anderen Anwendung. Sprache, Sitzung und Programmversion können Meldungen und Verhalten verändern.

## 6. Typische Anwendungsfälle

Desktopskripte nachvollziehen: Argumente, Ausgabe und Rückgabestatus vor einer echten Integration getrennt betrachten. Fehler eingrenzen: Erst die dokumentierte Schnittstelle der installierten Variante mit den Anforderungen des Skripts vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Installations- und default-Aufrufe verändern echte Benutzer- oder Systemzuordnungen. Externe XML-Dateien und Desktopstarter nicht ungeprüft verwenden. Ein ermittelter MIME-Typ ist keine Schadcodeprüfung; Dateiinhalte dürfen nicht allein wegen ihrer Endung geöffnet werden. Keine Ausführung mit sudo: Das würde einen anderen Benutzerkontext betreffen und ersetzt keine passende Sitzung.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Werkzeug fehlt, Status 3 | Benötigter Desktophelfer ist nicht verfügbar. |
| Datei fehlt, Status 2 | Pfad und Arbeitsverzeichnis prüfen. |
| Standard wurde nicht übernommen | Anwendungsregistrierung, unterstützte Typen und Desktoppolitik prüfen; Änderung nicht blind wiederholen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zunächst lokale Hilfe und verfügbare Variante prüfen. Benutzereingaben als Daten behandeln, zitieren und vor Weiterverarbeitung validieren. Abbruch und technische Fehler dürfen nicht still als Zustimmung gelten.

**Prüfstand am 2026-11-13:** xdg-mime 1.1.3. Praktisch geprüft: GUI-/Sitzungsintegration, echte Benutzerreaktionen und Änderungen bleiben praktisch offen. Nur die Hilfe/Version wurde lokal aufgerufen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gio mime` | Alternative GIO-Zuordnungssicht. |
| `xdg-open` | Öffnet über die Zuordnung und startet Programme. |
| `file` | Weitere Dateityperkennung ohne Standardhandlerverwaltung. |

Ausgangsdatensatz 264 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
