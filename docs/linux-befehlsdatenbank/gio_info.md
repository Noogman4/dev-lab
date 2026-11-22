---
id: "gio_info"
name: "gio-info"
command: "gio info"
category: "Desktop & GUI"
language: "de"
root_required: false
risk_level: "safe"
tags: ["Desktop & GUI", "gio-info"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 258
reviewed_at: "2026-11-13"
locally_checked_version: "gio / GLib 2.80.0"
---

# gio-info – GIO-Metadaten gezielt abfragen

## 1. Kurzbeschreibung

Der Katalogname `gio-info` bezeichnet hier den Unterbefehl **`gio info`**, kein vorauszusetzendes eigenes Programm. Kennung und Anzeigename aus dem Katalog bleiben erhalten; command enthält die tatsächliche Syntax. Eigene lokale Dateien benötigen kein Root.

## 2. Was macht der Befehl?

`gio info` beschreibt Attribute eines Orts, statt dessen Nutzinhalt auszugeben. Namen sind in Namensräumen wie standard:: oder unix:: organisiert. Ein Metadatenbericht beweist keine Inhaltsgleichheit. Fehlende Attribute können bedeuten, dass der Backend sie nicht liefert; sie dürfen nicht als Nullwerte geraten werden.

GIO kann lokale Pfade oder von Backends unterstützte URIs verarbeiten. Ein Doppelpunkt in einem bloßen Dateinamen kann als URI-Schema verstanden werden; einen lokalen Namen dann ausdrücklich mit ./ oder absolutem Pfad angeben. Die Übung verwendet GIO_USE_VFS=local nur für die jeweiligen Prozesse und ausschließlich eigene lokale Daten.

Quelle, am 2026-11-13 gelesen: [GIO-Werkzeughandbuch](https://manpages.debian.org/trixie/libglib2.0-bin/gio.1.en.html), [GIO-Umgebung/local-VFS](https://docs.gtk.org/gio/overview.html) sowie lokale Manpage und Unterbefehlshilfe

## 3. Syntax

```text
gio info [OPTIONEN] ORT ...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-a LISTE` | Attributnamen oder Namensräume kommasepariert auswählen; Sternmuster zitieren. |
| `-n` | Symlink selbst statt dessen Ziel abfragen. |
| `-f` | Informationen zum Dateisystem statt nur zum Dateiobjekt. |
| `-w` | Schreibbare Attribute auflisten; schreibt diese nicht. |
| `gio help info` | Verfügbare lokale Optionen lesen. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash, GLib/gio und ein beschreibbarer temporärer Bereich. Alle Schritte in derselben Shell ausführen. GIO_USE_VFS=local wählt den eingebauten lokalen VFS statt GVfs; es wird keine entfernte URI benutzt.

### Schritt 1: Neue Testdatei erzeugen

### Schritt 2: Unterbefehl auf diese Datei beziehungsweise diesen Ordner anwenden

```bash
uebung="$(mktemp -d -t netmon-gio-info-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf 'Test\n' > 'Meine Notiz.txt'
GIO_USE_VFS=local gio info -a 'standard::type,standard::size' "$uebung/Meine Notiz.txt"
cat 'Meine Notiz.txt'
```

### Schritt 3: Ausgabe auswerten

Die ausgewählten Attribute nennen eine reguläre Datei und Größe 5, zum Schluss steht weiterhin `Test`. Zusätzliche Kopfzeilen können URI oder lokalen Pfad zeigen. Die Größenangabe ist die Dateilänge, nicht der belegte Speicher ganzer Verzeichnisse. Es wurden keine Attribute gesetzt. Der Testordner bleibt zur Kontrolle bestehen. Dies ist kein Test von Netzwerkbackends, Mounts oder Desktopanwendungen.

## 6. Typische Anwendungsfälle

**Lokale Daten bearbeiten:** Den beschriebenen Unterbefehl gezielt einsetzen, statt den ähnlich aussehenden Katalognamen blind aufzurufen. **Skripte verstehen:** GIO-Orte und gewöhnliche Shellargumente auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Weite Attributmuster können persönliche Pfade, Zugriffs- oder Sicherheitsinformationen anzeigen. -n ändert die Frage bei Links. Eine als schreibbar gemeldete Attributklasse ist keine Erlaubnis, sie zu verändern. Fremde URIs können Netzwerkverkehr oder Sitzungsdienste auslösen. Hier wurden weder reale Benutzerdateien noch entfernte Orte verwendet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| `gio-info: command not found` | Tatsächliche Syntax ist gio info. |
| Operation not supported | Gewählter Backend/Ort unterstützt die Funktion nicht; keine unkontrollierten Folgeaktionen. |
| Falscher Ort | Arbeitsverzeichnis, Zitierung und URI-Erkennung prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit konkreten eigenen Pfaden beginnen. Ergebnis und Rückgabestatus gemeinsam kontrollieren; ein vertraut aussehender Name beweist keinen Inhalt. Einstellungen und Backends des realen Desktops werden nicht umkonfiguriert.

**Prüfstand am 2026-11-13:** gio / GLib 2.80.0. Praktisch geprüft: Abschnitt 5 mit eigener temporärer Datei und lokalem VFS ausgeführt. Nicht praktisch geprüft: andere Backends, entfernte URIs, fremde Berechtigungen und andere Versionen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gio help info` | Hilfe des tatsächlichen Unterbefehls. |
| `gio` | Übergeordnetes Werkzeug mit auch schreibenden Unterbefehlen. |
| `stat` | Andere Metadatensicht auf lokale Dateien. |

Ausgangsdatensatz 258 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
