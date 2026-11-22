---
id: "gio_list"
name: "gio-list"
command: "gio list"
category: "Desktop & GUI"
language: "de"
root_required: false
risk_level: "safe"
tags: ["Desktop & GUI", "gio-list"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 259
reviewed_at: "2026-11-13"
locally_checked_version: "gio / GLib 2.80.0"
---

# gio-list – Verzeichniseinträge mit gio list auflisten

## 1. Kurzbeschreibung

Der Katalogname `gio-list` bezeichnet hier den Unterbefehl **`gio list`**, kein vorauszusetzendes eigenes Programm. Kennung und Anzeigename aus dem Katalog bleiben erhalten; command enthält die tatsächliche Syntax. Eigene lokale Dateien benötigen kein Root.

## 2. Was macht der Befehl?

`gio list` zeigt die direkten Kinder der angegebenen Orte. Ohne Ort wird das aktuelle Verzeichnis betrachtet. Es ist keine automatische rekursive Baumansicht und kein Inhaltsvergleich. Anzeigenamen können von technisch verwendeten Namen abweichen; sie sind nicht ohne Prüfung als Dateiprotokoll für ein Skript geeignet.

GIO kann lokale Pfade oder von Backends unterstützte URIs verarbeiten. Ein Doppelpunkt in einem bloßen Dateinamen kann als URI-Schema verstanden werden; einen lokalen Namen dann ausdrücklich mit ./ oder absolutem Pfad angeben. Die Übung verwendet GIO_USE_VFS=local nur für die jeweiligen Prozesse und ausschließlich eigene lokale Daten.

Quelle, am 2026-11-13 gelesen: [GIO-Werkzeughandbuch](https://manpages.debian.org/trixie/libglib2.0-bin/gio.1.en.html), [GIO-Umgebung/local-VFS](https://docs.gtk.org/gio/overview.html) sowie lokale Manpage und Unterbefehlshilfe

## 3. Syntax

```text
gio list [OPTIONEN] [ORT ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-h`, `--hidden` | Versteckte Einträge zeigen; -h ist hier keine Hilfeoption. |
| `-l` | Lange Listenform verwenden. |
| `-a LISTE` | Zusätzliche Attribute gezielt anfordern. |
| `-n` | Symbolischen Links nicht folgen. |
| `-d` | Anzeigenamen statt gewöhnlicher Namen darstellen. |
| `-u` | Vollständige URIs ausgeben; Escape-Darstellung beachten. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash, GLib/gio und ein beschreibbarer temporärer Bereich. Alle Schritte in derselben Shell ausführen. GIO_USE_VFS=local wählt den eingebauten lokalen VFS statt GVfs; es wird keine entfernte URI benutzt.

### Schritt 1: Neue Testdatei erzeugen

### Schritt 2: Unterbefehl auf diese Datei beziehungsweise diesen Ordner anwenden

```bash
uebung="$(mktemp -d -t netmon-gio-list-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf 'Test\n' > 'Meine Notiz.txt'
printf 'Intern\n' > .intern
GIO_USE_VFS=local gio list "$uebung"
GIO_USE_VFS=local gio list -h "$uebung"
```

### Schritt 3: Ausgabe auswerten

Die erste Liste zeigt `Meine Notiz.txt`, die zweite zusätzlich `.intern`. Reihenfolge und Darstellung sind nicht fest zugesichert. Es wurden nur direkte Kinder gelesen. Ein Name mit Leerzeichen bleibt ein Name, obwohl eine ungeeignete nachträgliche Shellaufteilung ihn zerlegen könnte. Der Testordner bleibt zur Kontrolle bestehen. Dies ist kein Test von Netzwerkbackends, Mounts oder Desktopanwendungen.

## 6. Typische Anwendungsfälle

**Lokale Daten bearbeiten:** Den beschriebenen Unterbefehl gezielt einsetzen, statt den ähnlich aussehenden Katalognamen blind aufzurufen. **Skripte verstehen:** GIO-Orte und gewöhnliche Shellargumente auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Listen können private Namen offenlegen. Menschenlesbare oder URI-escaped Ausgabe nicht mit einem NUL-getrennten Pfadprotokoll verwechseln. Große Ordner und zusätzliche Attribute erhöhen den Aufwand. Fremde URIs können Netzwerkverkehr oder Sitzungsdienste auslösen. Hier wurden weder reale Benutzerdateien noch entfernte Orte verwendet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| `gio-list: command not found` | Tatsächliche Syntax ist gio list. |
| Operation not supported | Gewählter Backend/Ort unterstützt die Funktion nicht; keine unkontrollierten Folgeaktionen. |
| Falscher Ort | Arbeitsverzeichnis, Zitierung und URI-Erkennung prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit konkreten eigenen Pfaden beginnen. Ergebnis und Rückgabestatus gemeinsam kontrollieren; ein vertraut aussehender Name beweist keinen Inhalt. Einstellungen und Backends des realen Desktops werden nicht umkonfiguriert.

**Prüfstand am 2026-11-13:** gio / GLib 2.80.0. Praktisch geprüft: Abschnitt 5 mit eigener temporärer Datei und lokalem VFS ausgeführt. Nicht praktisch geprüft: andere Backends, entfernte URIs, fremde Berechtigungen und andere Versionen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gio help list` | Hilfe des tatsächlichen Unterbefehls. |
| `gio` | Übergeordnetes Werkzeug mit auch schreibenden Unterbefehlen. |
| `stat` | Andere Metadatensicht auf lokale Dateien. |

Ausgangsdatensatz 259 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
