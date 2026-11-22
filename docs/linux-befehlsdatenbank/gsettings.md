---
id: "gsettings"
name: "gsettings"
command: "gsettings"
category: "Desktop & GUI"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Desktop & GUI", "gsettings"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 261
reviewed_at: "2026-11-13"
locally_checked_version: "GLib 2.80.0"
---

# gsettings – Schemaabhängige Einstellungen lesen und gezielt ändern

## 1. Kurzbeschreibung

GSettings stellt typisierte Anwendungseinstellungen bereit. gsettings kann lesen, beobachten und schreiben; die ursprüngliche Einstufung als ausschließlich lesend ist falsch. Normale Einstellungen gehören zur Benutzersitzung, nicht zu Root.

## 2. Was macht der Befehl?

Ein Schema definiert Schlüssel, Datentypen, Vorgaben und gegebenenfalls Wertebereiche. Die Schema-ID ist vom Speicherpfad zu unterscheiden. Relokierbare Schemata benötigen zusätzlich einen Pfad. Werte werden als GVariant-Text dargestellt; bei Strings sind deshalb sowohl Shellzitierung als auch innere GVariant-Anführungszeichen zu beachten. reset entfernt eine Benutzerüberschreibung und stellt die wirksame Vorgabe wieder her; es garantiert nicht die Wiederherstellung eines früheren Wertes.

Quelle, am 2026-11-13 gelesen: [GSettings-Handbuch](https://manpages.debian.org/trixie/libglib2.0-bin/gsettings.1.en.html), [GSettings-Schemata](https://docs.gtk.org/gio/class.Settings.html) und lokale Manpage

## 3. Syntax

```text
gsettings [--schemadir VERZEICHNIS] BEFEHL SCHEMA[:PFAD] [SCHLUESSEL] [WERT]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `get`, `range`, `describe` | Wert, zulässigen Typ/Bereich und Beschreibung abfragen. |
| `writable` | Schreibbarkeit abfragen; kein Änderungsauftrag. |
| `set` | Typgerechten Wert setzen; kann laufende Anwendungen beeinflussen. |
| `reset`, `reset-recursively` | Überschreibungen einzeln oder für das Schema zurücksetzen; rekursiv besonders weitreichend. |
| `monitor` | Dauerhaft Änderungen beobachten, mit Strg+C beenden. |
| `--schemadir` | Zusätzlichen Schemaordner verwenden; allein keine Speicherisolation. |
| `GSETTINGS_BACKEND=memory` | Nur im jeweiligen Prozess nicht persistent speichern; kein geteilter Speicher zwischen CLI-Aufrufen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigenes Schema isoliert vorbereiten

Voraussetzungen: Bash, GLib-Werkzeuge. Keine echten Desktop-Schemata und keine schreibenden gsettings-Aufrufe.

```bash
uebung="$(mktemp -d -t lernen-gsettings-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
cat > org.example.Lernen.gschema.xml <<'XML'
<schemalist>
  <schema id="org.example.Lernen" path="/org/example/lernen/">
    <key name="farbe" type="s"><default>'blau'</default></key>
  </schema>
</schemalist>
XML
glib-compile-schemas --strict .
GSETTINGS_BACKEND=memory gsettings --schemadir "$uebung" get org.example.Lernen farbe
GSETTINGS_BACKEND=memory gsettings --schemadir "$uebung" range org.example.Lernen farbe
```

### Schritt 2: Ergebnis verstehen

Die Ausgabe lautet im Test `'blau'` und `type s`. Das XML wird nur im eigenen Ordner kompiliert. Der Memory-Backend verhindert den Zugriff auf persistente Benutzerwerte. --schemadir allein würde dies nicht leisten.

### Schritt 3: Grenzen beachten

Ein set in einem eigenen Memory-Prozess wäre beim nächsten gsettings-Prozess schon verloren. Dieser Test belegt nur Kompilierung, Lesen des Vorgabewertes und Typabfrage des eigenen Schemas, keine dconf-Sitzungsintegration.

## 6. Typische Anwendungsfälle

Anwendungskonfiguration diagnostizieren: Schema und Schlüssel vor Änderungen prüfen. Eigene Software entwickeln: Vorgaben und Datentypen eines neuen Schemas ohne Installation nachvollziehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Setzen und rekursives Zurücksetzen können viele echte Benutzereinstellungen verändern. dconf-Schreibvorgänge benötigen üblicherweise den Sitzungsbus. sudo erzeugt keinen passenden Desktopkontext. Fremde Schema- oder Programmdateien nicht blind ausführen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| No such schema | Schema-ID und kompilierten Schemaordner prüfen. |
| Wert hat falschen Typ | range lesen und GVariant-Zitierung prüfen. |
| Set scheint verschwunden | Memory-Backend ist pro Prozess; persistente Backends haben andere Regeln. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit get, range und describe beginnen. Vor echten Änderungen vorherigen Wert und Umgebung dokumentieren. Den hier gesetzten Memory-Backend nicht mit einem dauerhaften Testprofil verwechseln.

**Prüfstand am 2026-11-13:** GLib 2.80.0. Praktisch geprüft: Eigenes Schema kompiliert, Memory-Vorgabewert und Typ gelesen. Praktische Änderungen echter Einstellungen, D-Bus-Schreiben und Monitoring bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `dconf` | Darunterliegender Konfigurationsspeicher ohne dieselbe Schemaabstraktion. |
| `glib-compile-schemas` | Kompiliert die eigenen XML-Schemata. |
| `gio` | Weitere GLib-Werkzeuge. |

Ausgangsdatensatz 261 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
