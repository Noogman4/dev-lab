---
id: "gio"
name: "gio"
command: "gio"
category: "Desktop & GUI"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Desktop & GUI", "gio"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 255
reviewed_at: "2026-11-13"
locally_checked_version: "gio / GLib 2.80.0"
---

# gio – GIO-Unterbefehle nach ihrer Wirkung auswählen

## 1. Kurzbeschreibung

`gio` stellt Dateifunktionen der GLib/GIO-Bibliothek bereit. Einige Unterbefehle lesen, andere kopieren, löschen, mounten, starten Programme oder ändern Dateizuordnungen. Eigene lokale Dateien brauchen kein Root; GIO ist deshalb trotzdem nicht pauschal sicher lesend.

## 2. Was macht der Befehl?

Im Gegensatz zu rein lokalen Werkzeugen können GIO-Orte auch URIs eines Backends sein. Deren Verwendung kann Netz-/Authentifizierungs- oder Sitzungsaktionen auslösen. Dateinamen mit Doppelpunkt können als URI gelesen werden. Ein expliziter relativer ./-Pfad oder absoluter Pfad vermeidet diese Mehrdeutigkeit bei lokalen Daten.

Quelle, am 2026-11-13 gelesen: [GIO-Werkzeughandbuch](https://manpages.debian.org/trixie/libglib2.0-bin/gio.1.en.html), [offizielle GIO-Übersicht](https://docs.gtk.org/gio/overview.html), lokale Manpage

## 3. Syntax

```text
gio UNTERBEFEHL [OPTIONEN] [ORTE ...]
gio help [UNTERBEFEHL]
gio version
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `help`, `version` | Hilfe beziehungsweise GLib-Version lesen; nicht jeden Unterbefehl mit --help gleichsetzen. |
| `cat`, `info`, `list` | Dateiinhalte, Metadaten oder Verzeichnisnamen lesen. |
| `copy`, `move`, `remove`, `save` | Dateien schreiben, verschieben oder entfernen. |
| `open`, `launch` | Andere Anwendungen starten, kein bloßer Inhaltstest. |
| `mime TYP [HANDLER]` | Zuordnung lesen oder mit Handler ändern. |
| `mount`, `trash` | Sitzungs-/Datenträgerzugriff oder Papierkorbverwaltung; eigene Wirkungsgrenzen. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und GLib/gio. Es wird nur eine neue lokale Textdatei verwendet.

### Schritt 1: Übungsdatei anlegen

### Schritt 2: Version/Hilfe lesen und eigenen Inhalt anzeigen

```bash
uebung="$(mktemp -d -t netmon-gio-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf 'Test\n' > notiz.txt
gio version
gio help cat
GIO_USE_VFS=local gio cat "$uebung/notiz.txt"
```

### Schritt 3: Ergebnis unterscheiden

Version und Hilfe beschreiben das Werkzeug; nur cat liest die notiz.txt. Erwartet steht zuletzt `Test`. GIO_USE_VFS=local gilt für diesen einen Aufruf und vermeidet GVfs für die Dateioperation. Es wird kein Browser und keine Desktopanwendung gestartet.

## 6. Typische Anwendungsfälle

**Lokale Dateiaufgaben:** Eine passende konkrete Funktion wählen. **Backendvergleich:** Gleiche Operation auf lokalen und entfernten Orten erst in getrennten autorisierten Tests beurteilen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein Unterbefehl kann Daten verlieren lassen oder Programme starten. URI-Schemata nicht aus fremden Texten ungeprüft übernehmen. Papierkorb ist keine unabhängige Sicherung. Keine echten Benutzer-/MIME-/Mountkonfigurationen und keine entfernten Quellen in dieser Übung.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Unbekannter Unterbefehl | gio help lesen, Katalogalias nicht als eigenes Programm voraussetzen. |
| Unbekanntes Protokoll | Doppelpunkt wurde als URI erkannt oder Backend fehlt. |
| Zugriff benötigt Sitzung | GVfs/Backend kann Sessionbus brauchen; reine lokale Übung mit local-VFS begrenzen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Vor jeder Operation den Unterbefehl und dessen lokale Hilfe prüfen. Dateischreibzugriffe und Appstarts sind verschiedene Freigaben.

**Prüfstand am 2026-11-13:** gio / GLib 2.80.0. Praktisch geprüft: Version, cat-Hilfe und cat eigener temporärer Datei mit local-VFS erfolgreich. Schreibende Unterbefehle, GVfs, Apps und entfernte URIs nicht praktisch geprüft. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `cat` | Lokaler Inhaltsleser. |
| `cp` | Lokales Kopierwerkzeug. |
| `xdg-open` | Anwendungsstart, keine reine Dateianzeige im Terminal. |

Ausgangsdatensatz 255 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
