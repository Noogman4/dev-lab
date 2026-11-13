---
id: "xdg_settings"
name: "xdg-settings"
command: "xdg-settings"
category: "Desktop & GUI"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Desktop & GUI", "xdg-settings"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 266
reviewed_at: "2026-11-13"
locally_checked_version: "xdg-settings 1.1.3"
---

# xdg-settings – Desktopvorgaben abfragen, prüfen und setzen

## 1. Kurzbeschreibung

xdg-settings vermittelt ausgewählte Eigenschaften der Desktopumgebung. get und check lesen beziehungsweise vergleichen; set verändert Vorgaben. Es ist keine universelle Schnittstelle für jede beliebige Desktopoption.

## 2. Was macht der Befehl?

Eine Eigenschaft kann allein vollständig sein, etwa default-web-browser. default-url-scheme-handler benötigt zusätzlich das Schema, etwa mailto. Als Anwendungswert dient eine Desktop-Dateikennung. get und check beantworten verschiedene Fragen: Eine angezeigte Browserkennung kann mit uneinheitlichen darunterliegenden Zuordnungen zusammenfallen, weshalb check trotz passendem get-Ergebnis fehlschlagen kann.

Quelle, am 2026-11-13 gelesen: [xdg-utils: xdg-settings](https://portland.freedesktop.org/doc/xdg-settings.html) und lokale Manpage

## 3. Syntax

```text
xdg-settings get EIGENSCHAFT [UNTEREIGENSCHAFT]
xdg-settings check EIGENSCHAFT [UNTEREIGENSCHAFT] WERT
xdg-settings set EIGENSCHAFT [UNTEREIGENSCHAFT] WERT
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `get` | Wirksamen Wert erfragen. |
| `check` | Unterliegende Einstellungen gegen gewünschten Wert prüfen; Antwort auswerten. |
| `set` | Desktopvorgabe ändern; hier nicht ausgeführt. |
| `--list` | Bekannte Eigenschaften auflisten, keine Vollständigkeitsgarantie für jeden Desktop. |
| `--help`, `--manual`, `--version` | Schnittstelle beziehungsweise Werkzeugversion lesen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen prüfen

Das folgende Muster ist eine Leseübung. Eine funktionierende passende Benutzersitzung und die installierte Implementierung wären Voraussetzungen für die echte Nutzung. Hier werden weder Dialoge noch Benachrichtigungen ausgelöst, Anwendungen gestartet oder Benutzereinstellungen verändert.

### Schritt 2: Muster lesen

**Nicht ausgeführt; keine gemessene Ausgabe:**

```text
xdg-settings get default-web-browser
xdg-settings check default-web-browser beispiel.desktop
```

beispiel.desktop ist ein erklärender Platzhalter für eine tatsächlich installierte Desktop-Dateikennung. Beide Abfragen bleiben hier unausgeführt. Eine check-Antwort ist mit Rückgabestatus und Fehlermeldungen zu lesen; sie startet keinen Browser. Ein set-Aufruf wäre bereits eine eigene Änderung.

### Schritt 3: Ergebnisgrenze verstehen

Ein Exitstatus beschreibt den jeweiligen Werkzeugaufruf. Er beweist keine nachfolgende Benutzeraktion oder erfolgreiche Verarbeitung in einer anderen Anwendung. Sprache, Sitzung und Programmversion können Meldungen und Verhalten verändern.

## 6. Typische Anwendungsfälle

Desktopskripte nachvollziehen: Argumente, Ausgabe und Rückgabestatus vor einer echten Integration getrennt betrachten. Fehler eingrenzen: Erst die dokumentierte Schnittstelle der installierten Variante mit den Anforderungen des Skripts vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Eine geänderte Browser- oder Protokollzuordnung beeinflusst nachfolgende Öffnungsvorgänge. Fremde Desktopstarter können beliebige Anwendungen aufrufen. Nicht jede Desktopumgebung implementiert dieselben Eigenschaften oder Helfer. Keine systemweiten Konfigurationsänderungen zur Behebung eines bloßen Abfragefehlers. Keine Ausführung mit sudo: Das würde einen anderen Benutzerkontext betreffen und ersetzt keine passende Sitzung.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Unbekannte Eigenschaft | --list und lokale Version prüfen. |
| get passt, check nicht | Mehrere zugrunde liegende Zuordnungen können uneinheitlich sein. |
| Wert hat falsche Form | Desktop-Dateikennung statt Programmpfad verwenden; Protokollschema separat angeben. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zunächst lokale Hilfe und verfügbare Variante prüfen. Benutzereingaben als Daten behandeln, zitieren und vor Weiterverarbeitung validieren. Abbruch und technische Fehler dürfen nicht still als Zustimmung gelten.

**Prüfstand am 2026-11-13:** xdg-settings 1.1.3. Praktisch geprüft: GUI-/Sitzungsintegration, echte Benutzerreaktionen und Änderungen bleiben praktisch offen. Nur die Hilfe/Version wurde lokal aufgerufen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `xdg-mime` | MIME-spezifische Handlerzuordnung. |
| `xdg-open` | Benutzt Desktopvorgaben zum Starten. |
| `gsettings` | Schemaabhängige Konfiguration statt xdg-utils-Eigenschaften. |

Ausgangsdatensatz 266 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
