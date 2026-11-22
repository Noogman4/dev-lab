---
id: "lsattr"
name: "lsattr"
command: "lsattr"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "safe"
tags: ["Datentraeger & Dateisysteme", "lsattr"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 225
reviewed_at: "2026-11-13"
locally_checked_version: "lsattr 1.47.0 (5-Feb-2023)"
---

# lsattr – Besondere Dateiattribute lesen

## 1. Kurzbeschreibung

`lsattr` zeigt Dateisystemattribute an, statt sie zu verändern. Für eigene erreichbare Dateien ist kein Root nötig. Es ergänzt die klassische Rechteanzeige von ls und ACL-Werkzeugen, ersetzt sie aber nicht.

## 2. Was macht der Befehl?

Buchstaben kennzeichnen gesetzte Flags, Bindestriche nicht gesetzte Positionen. Welche Attribute verfügbar sind, hängt von Dateisystem und Kernel ab. Ein `e` kann etwa Extent-Abbildung bedeuten und ist kein Fehlerkennzeichen. Nicht alle angezeigten Eigenschaften lassen sich mit chattr verändern. Die Online-Manpage 1.47.2 und lokale Manpage 1.47.0 wurden verglichen; Bedeutungen der Flags stehen im zugehörigen chattr-Handbuch.

Quelle, am 2026-11-13 gelesen: [lsattr-Handbuch](https://manpages.debian.org/trixie/e2fsprogs/lsattr.1.en.html), [Attributbedeutungen](https://manpages.debian.org/trixie/e2fsprogs/chattr.1.en.html) und lokale Manpage

## 3. Syntax

```text
lsattr [OPTIONEN] [DATEI_ODER_VERZEICHNIS ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-a` | Auch Punktnamen in Verzeichnissen anzeigen. |
| `-d` | Verzeichnis selbst statt seines Inhalts anzeigen. |
| `-R` | Unterverzeichnisse rekursiv lesen; großer Ausgabeumfang. |
| `-l` | Lange Attributnamen statt Buchstaben ausgeben. |
| `-p` | Projektkennung zusätzlich anzeigen. |
| `-v` | Dateigeneration anzeigen; keine Programmversion. |
| `-V` | Programmversion anzeigen. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash, e2fsprogs und ein unterstütztes lokales Dateisystem. Es werden nur eigene neu erzeugte Testdateien gelesen.

### Schritt 1: Testbestand anlegen und Felder lesen

```bash
uebung="$(mktemp -d -t netmon-lsattr-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
mkdir daten
printf 'Probe\n' > daten/notiz.txt
printf 'Verborgen\n' > daten/.intern
lsattr -V daten/notiz.txt
lsattr -a daten
lsattr -d daten
lsattr -l daten/notiz.txt
cat daten/notiz.txt
```

### Schritt 2: Ansichten unterscheiden

Die Einzelansicht zeigt `notiz.txt`, `-a` zusätzlich `.intern`, `-d` eine Zeile für `daten`. Die Buchstaben können je nach Dateisystem anders aussehen; sie sind keine fest zugesicherte Zeichenfolge. Mit `-l` werden unterstützte Namen ausgeschrieben.

### Schritt 3: Inhalt kontrollieren

Zum Schluss erscheint unverändert `Probe`. Das zeigt nur Inhaltserhalt im kleinen Beispiel, nicht eine vollständige Prüfung aller Metadaten oder Zugriffsregeln. Der temporäre Bestand bleibt erhalten.

## 6. Typische Anwendungsfälle

**Schreibfehler erklären:** Attribute wie immutable von normalen Modusbits unterscheiden. **Bestandsaufnahme:** Einen gezielt ausgewählten eigenen Dateisatz vor einer geplanten Änderung dokumentieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Attribute und Dateinamen können vertrauliche Informationen enthalten. Rekursion erweitert den gelesenen Bereich. Fehlende Unterstützung eines Attribut-ioctls ist kein Beleg für beschädigte Nutzdaten. Aus einer Anzeige folgt keine Erlaubnis, Flags mit chattr zu entfernen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Operation not supported | Dateisystem bietet die Abfrage nicht; als offene Implementierungsgrenze behandeln. |
| Verzeichnisinhalt statt Ordnerflag | -d verwenden. |
| Erwarteter Punktname fehlt | -a erforderlich. |
| Schreiben trotz unauffälliger Flags unmöglich | Modusbits, ACLs, Mountoptionen und andere Regeln zusätzlich prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Kleine explizite Pfade statt systemweiter Rekursion wählen. Lange Namen helfen beim Verstehen; abgespeicherte Anzeigen sind kein dauerhafter Zustandsnachweis.

**Prüfstand am 2026-11-13:** lsattr 1.47.0 (5-Feb-2023). Praktisch geprüft: Beispiel komplett an eigenen Dateien: Einzelansicht, Punktname, Verzeichnis selbst und lange Namen erfolgreich. Andere Dateisysteme, privilegierte Fälle und Spezialattribute nicht praktisch geprüft. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `chattr` | Attribute verändern. |
| `stat` | Andere Metadaten lesen. |
| `getfacl` | ACLs anzeigen. |

Ausgangsdatensatz 225 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
