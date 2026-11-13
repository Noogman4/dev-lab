---
id: "gio_copy"
name: "gio-copy"
command: "gio copy"
category: "Desktop & GUI"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Desktop & GUI", "gio-copy"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 257
reviewed_at: "2026-11-13"
locally_checked_version: "gio / GLib 2.80.0"
---

# gio-copy – Dateien mit gio copy gezielt kopieren

## 1. Kurzbeschreibung

Der Katalogname `gio-copy` bezeichnet hier den Unterbefehl **`gio copy`**, kein vorauszusetzendes eigenes Programm. Kennung und Anzeigename aus dem Katalog bleiben erhalten; command enthält die tatsächliche Syntax. Eigene lokale Dateien benötigen kein Root.

## 2. Was macht der Befehl?

`gio copy` schreibt eine oder mehrere Quelldateien an ein Ziel. Bei mehreren Quellen muss das Ziel ein Verzeichnis sein. Quellen werden nicht wie bei move entfernt. Der ähnliche Name zu cp bedeutet nicht, dass jede cp-Option verfügbar ist; eine rekursive Sicherung ganzer Bäume darf daraus nicht vorausgesetzt werden.

GIO kann lokale Pfade oder von Backends unterstützte URIs verarbeiten. Ein Doppelpunkt in einem bloßen Dateinamen kann als URI-Schema verstanden werden; einen lokalen Namen dann ausdrücklich mit ./ oder absolutem Pfad angeben. Die Übung verwendet GIO_USE_VFS=local nur für die jeweiligen Prozesse und ausschließlich eigene lokale Daten.

Quelle, am 2026-11-13 gelesen: [GIO-Werkzeughandbuch](https://manpages.debian.org/trixie/libglib2.0-bin/gio.1.en.html), [GIO-Umgebung/local-VFS](https://docs.gtk.org/gio/overview.html) sowie lokale Manpage und Unterbefehlshilfe

## 3. Syntax

```text
gio copy [OPTIONEN] QUELLE ... ZIEL
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-i` | Vor Überschreiben fragen; braucht eine passende Interaktion. |
| `-b` | Bestehende Zielversion sichern; kein vollständiges Backupkonzept. |
| `-T` | Ziel als direkten Dateipfad behandeln, nicht hinein kopieren. |
| `-P` | Symbolischen Links nicht folgen. |
| `--preserve` | Attribute möglichst erhalten; Backend-/Rechtegrenzen beachten. |
| `--default-permissions` | Prozessvorgaben statt Quellrechte für Ziel wählen. |
| `-p` | Fortschritt melden; kein Integritätsnachweis. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash, GLib/gio und ein beschreibbarer temporärer Bereich. Alle Schritte in derselben Shell ausführen. GIO_USE_VFS=local wählt den eingebauten lokalen VFS statt GVfs; es wird keine entfernte URI benutzt.

### Schritt 1: Neue Testdatei erzeugen

### Schritt 2: Unterbefehl auf diese Datei beziehungsweise diesen Ordner anwenden

```bash
uebung="$(mktemp -d -t netmon-gio-copy-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf 'Test\n' > 'Meine Notiz.txt'
GIO_USE_VFS=local gio copy "$uebung/Meine Notiz.txt" "$uebung/kopie.txt"
cmp -- "Meine Notiz.txt" kopie.txt
cat kopie.txt
```

### Schritt 3: Ausgabe auswerten

Erwartet ist `Test`; cmp bestätigt bytegleiche Quelle und Kopie. Der Zielname ist im neuen Ordner noch nicht vorhanden. Das prüft weder Überschreibabfrage noch vollständige Metadatenwiederherstellung. Eine erneute Kopie auf ein vorhandenes Ziel wäre ein gesonderter Konfliktfall. Der Testordner bleibt zur Kontrolle bestehen. Dies ist kein Test von Netzwerkbackends, Mounts oder Desktopanwendungen.

## 6. Typische Anwendungsfälle

**Lokale Daten bearbeiten:** Den beschriebenen Unterbefehl gezielt einsetzen, statt den ähnlich aussehenden Katalognamen blind aufzurufen. **Skripte verstehen:** GIO-Orte und gewöhnliche Shellargumente auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der Aufruf ist schreibend. Zielverwechslungen können vorhandene Daten betreffen. Attributerhalt ist kein Nachweis einer originalgetreuen Systemsicherung. -i ist kein Trockenlauf und eine Sicherungsdatei am selben Ort schützt nicht vor dessen Ausfall. Fremde URIs können Netzwerkverkehr oder Sitzungsdienste auslösen. Hier wurden weder reale Benutzerdateien noch entfernte Orte verwendet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| `gio-copy: command not found` | Tatsächliche Syntax ist gio copy. |
| Operation not supported | Gewählter Backend/Ort unterstützt die Funktion nicht; keine unkontrollierten Folgeaktionen. |
| Falscher Ort | Arbeitsverzeichnis, Zitierung und URI-Erkennung prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit konkreten eigenen Pfaden beginnen. Ergebnis und Rückgabestatus gemeinsam kontrollieren; ein vertraut aussehender Name beweist keinen Inhalt. Einstellungen und Backends des realen Desktops werden nicht umkonfiguriert.

**Prüfstand am 2026-11-13:** gio / GLib 2.80.0. Praktisch geprüft: Abschnitt 5 mit eigener temporärer Datei und lokalem VFS ausgeführt. Nicht praktisch geprüft: andere Backends, entfernte URIs, fremde Berechtigungen und andere Versionen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gio help copy` | Hilfe des tatsächlichen Unterbefehls. |
| `gio` | Übergeordnetes Werkzeug mit auch schreibenden Unterbefehlen. |
| `stat` | Andere Metadatensicht auf lokale Dateien. |

Ausgangsdatensatz 257 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
