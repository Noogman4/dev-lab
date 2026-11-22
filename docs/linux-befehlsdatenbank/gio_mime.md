---
id: "gio_mime"
name: "gio-mime"
command: "gio mime"
category: "Desktop & GUI"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Desktop & GUI", "gio-mime"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 260
reviewed_at: "2026-11-13"
locally_checked_version: "gio / GLib 2.80.0"
---

# gio-mime – MIME-Zuordnungen mit GIO verstehen

## 1. Kurzbeschreibung

Der eingefrorene Katalogname gio-mime wird als `gio mime` ausgeführt. Ohne zweites Argument werden Anwendungen zu einem MIME-Typ abgefragt; mit zweitem Argument wird die Standardanwendung geändert. Die Abfrage bestimmt nicht den Typ einer Datei.

## 2. Was macht der Befehl?

GIO arbeitet mit registrierten Desktop-Anwendungen. Ein Handler ist eine Desktop-Dateikennung einschließlich .desktop, kein beliebiger Shellbefehl und kein Pfad zu einer Nutzdatei. Registriert, empfohlen und Standard sind unterschiedliche Rollen. Welche Anwendungen sichtbar sind, hängt von Sitzung, installierten Desktop-Dateien und Benutzerzuordnungen ab.

Quelle, am 2026-11-13 gelesen: [GIO-Werkzeughandbuch](https://manpages.debian.org/trixie/libglib2.0-bin/gio.1.en.html) und lokale Unterbefehlshilfe

## 3. Syntax

```text
gio help mime
gio mime MIME-TYP [HANDLER.desktop]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `gio help mime` | Unterbefehlshilfe anzeigen, ohne eine Zuordnung anzufordern. |
| `MIME-TYP` | Beispielsweise text/plain; ohne Handler Zuordnungen abfragen. |
| `HANDLER.desktop` | Zusätzliches Positionsargument setzt den Standardhandler; echte Benutzeränderung. |
| `gio version` | GLib-Version anzeigen; kein Test der Desktopintegration. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Hilfe prüfen

```bash
gio help mime
```

Dieser Hilfeaufruf wurde ausgeführt. Er benötigt weder eine Testdatei noch eine Änderung an Dateizuordnungen.

### Schritt 2: Abfragemuster verstehen

Nicht ausgeführtes Muster:

```text
gio mime text/plain
```

Eine mögliche Antwort würde Standard, registrierte und empfohlene Anwendungen benennen. Konkrete Kennungen werden hier nicht als gemessene Ausgabe angegeben.

### Schritt 3: Schreibgrenze erkennen

Ein zusätzliches Argument wie eine Desktop-Dateikennung würde bereits eine Voreinstellung ändern. Es wird hier bewusst kein solcher Aufruf ausgeführt. Auch ein anschließendes gio open wäre ein eigener Programmstart.

## 6. Typische Anwendungsfälle

Zuordnungsprobleme eingrenzen: Zunächst MIME-Typ und Anwendungskatalog unterscheiden. Skripte prüfen: Die Anzahl der Positionsargumente entscheidet hier zwischen Abfrage und Einstellung.

## 7. Risiken, Nebenwirkungen und Vorsicht

Das zweite Argument verändert Benutzerverhalten für spätere Öffnungsvorgänge. Eine vertrauenswürdig klingende Desktop-Kennung beweist keine sichere Anwendung. Keine Handler aus fremden Dateien installieren und keine fremden URIs öffnen. Root ist für normale Benutzerzuordnungen nicht erforderlich und würde den falschen Kontext bearbeiten.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| gio-mime nicht gefunden | Es handelt sich um gio mime, nicht um ein eigenes vorausgesetztes Programm. |
| Kein Standardhandler | Registrierte oder empfohlene Anwendungen bedeuten nicht zwingend einen gesetzten Standard. |
| Dateityp unverändert | Zuordnung und Erkennung des Inhalts sind verschiedene Aufgaben. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Vor jeder echten Änderung die vorhandene Zuordnung und den Geltungsbereich gesondert festhalten. Hilfeaufrufe sind kein Nachweis funktionierender Anwendungsregistrierung.

**Prüfstand am 2026-11-13:** gio / GLib 2.80.0. Praktisch geprüft: Nur Unterbefehlshilfe ausgeführt. Praktische Abfragen echter Zuordnungen, Setzen eines Handlers und Anwendungsstarts bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gio info` | Dateimetadaten statt Zuordnungsverwaltung. |
| `xdg-mime` | Weiteres Desktopwerkzeug für Typen und Standards. |
| `gio open` | Startet die zugeordnete Anwendung; hier nicht getestet. |

Ausgangsdatensatz 260 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
