---
id: "dconf"
name: "dconf"
command: "dconf"
category: "Desktop & GUI"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Desktop & GUI", "dconf"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 254
reviewed_at: "2026-11-13"
locally_checked_version: "Paket dconf-cli vorhanden; Programmversionsausgabe nicht ermittelt"
---

# dconf – Direkte dconf-Werte und Offline-Kompilierung unterscheiden

## 1. Kurzbeschreibung

`dconf` liest und verändert eine Einstellungsdatenbank. Es verwendet dabei nicht automatisch die Schema-/Typprüfungen von GSettings. Normale eigene Benutzereinstellungen brauchen kein Root, können aber sofort den Desktop beeinflussen. Hier wird nur eine neue separate Binärdatei kompiliert.

## 2. Was macht der Befehl?

Schlüssel beginnen mit / und enden nicht damit, Verzeichnispräfixe beginnen und enden mit /. Werte werden als GVariant dargestellt: Ein String braucht zusätzlich zur Shellzitierung seine Wert-Anführungszeichen. write/load/reset können echte Einstellungen verändern; compile erzeugt dagegen eine Datenbankdatei aus einem gewählten Keyfile-Verzeichnis. update betrifft Systemdatenbanken.

Quelle, am 2026-11-13 gelesen: [dconf-Projekthandbuch bei Debian](https://manpages.debian.org/trixie/dconf-cli/dconf.1.en.html)

## 3. Syntax

```text
dconf read SCHLUESSEL
dconf list VERZEICHNIS/
dconf compile AUSGABE QUELLVERZEICHNIS
dconf help [UNTERBEFEHL]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `read`, `list` | Werte beziehungsweise direkte Untereinträge lesen. |
| `write` | GVariant-Wert schreiben; keine automatische GSettings-Schemaprüfung. |
| `reset -f` | Ganzes Präfix zurücksetzen; -f ist keine Trockenlaufoption. |
| `dump`, `load` | Teilbaum exportieren beziehungsweise importieren; load schreibt. |
| `compile` | Keyfiles in ausdrücklich gewählte neue Binärdatei übersetzen. |
| `watch` | Änderungen beobachten; kein statischer Dateitest. |
| `update` | Systemdatenbanken aktualisieren; hier ausgeschlossen. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und dconf-cli. Alle Dateien liegen neu im eigenen Temporärordner. Die erzeugte Datenbank wird nicht installiert, geladen oder in ein Benutzerprofil eingebunden.

### Schritt 1: Eigenes Keyfile schreiben und kompilieren

```bash
uebung="$(mktemp -d -t netmon-dconf-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
mkdir lernen.d
printf "[org/example/lernen]\nfarbe='blau'\n" > lernen.d/00-farbe
dconf compile "$uebung/lernen.db" "$uebung/lernen.d"
test -s lernen.db
printf 'Testdatenbank erzeugt\n'
```

### Schritt 2: Ergebnis kontrollieren

Erwartet erscheint `Testdatenbank erzeugt`. compile selbst beendet sich erfolgreich und erzeugt eine nichtleere lernen.db. Die Keyfilegruppe beschreibt einen erfundenen Pfad; der Wert ist der GVariant-String blau.

### Schritt 3: Begrenzen

Es wurde kein write, load, reset oder update ausgeführt. Die Dateierzeugung bestätigt keine wirksame Desktopkonfiguration und keine Prüfung gegen ein echtes GSettings-Schema. Testdateien bleiben erhalten.

## 6. Typische Anwendungsfälle

**Offline-Daten vorbereiten:** Struktur eines gesonderten Keyfiles verstehen. **Support:** Direkte gespeicherte Werte von schemaspezifischer Auslegung unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Schreibende Benutzeroperationen benötigen typischerweise Session-D-Bus und können Anwendungen beeinflussen. Rekursive Resets verlieren eigene Einstellungen. Ein dump kann vertrauliche Werte enthalten. Keine produktiven Pfade, Profile oder Systemdatenbanken verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Ungültiger Wert | GVariant-Zitierung und Datentyp prüfen. |
| Pfad ungültig | Schlüssel und Verzeichnispräfix unterscheiden. |
| Kein Bus bei write | Schreiboperation erfordert Sitzung; nicht zur Übung einen realen Dienst verändern. |
| Wert ohne Wirkung | Schema oder Anwendung erwartet anderen Ort/Typ. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Offline-Kompilierung und tatsächliche Integration getrennt behandeln. Ungeprüfte Datenbanken nicht in eigene Konfigurationsverzeichnisse kopieren.

**Prüfstand am 2026-11-13:** Paket dconf-cli vorhanden; Programmversionsausgabe nicht ermittelt. Praktisch geprüft: Nur Offline-compile eigener Keyfiles erfolgreich; keine Installation der DB. Benutzer-/Systemprofil, Typsemantik, Buszugriff und Desktopwirkung nicht praktisch geprüft. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gsettings` | Schemaorientierter Zugriff. |
| `dconf-editor` | GUI mit realen Einstellungswirkungen. |
| `dbus-send` | Kommunikation, kein Einstellungsprüfer. |

Ausgangsdatensatz 254 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
