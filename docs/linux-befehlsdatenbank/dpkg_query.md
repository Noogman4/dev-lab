---
id: "dpkg_query"
name: "dpkg-query"
command: "dpkg-query"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "dpkg-query"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 458
reviewed_at: "2026-11-13"
locally_checked_version: "dpkg-query 1.22.6"
---

# dpkg-query – Eine eigene Statusdatei ausdrücklich auswählen

## 1. Kurzbeschreibung

dpkg-query liest die dpkg-Datenbank. Ein gelisteter Datensatz und eine tatsächlich funktionsfähige Anwendung sind verschiedene Dinge. Mit --admindir lässt sich die lesende Abfrage auf eine eigene Testdatenbank begrenzen.

## 2. Was macht der Befehl?

--list zeigt gewünschte Aktion, Status und Fehlerkennzeichen; --show mit Format ist für gezielte Felder geeigneter. --listfiles nennt verwaltete Dateipfade, nicht zwingend alle zur Laufzeit erzeugten Dateien. Die Übung schreibt eine künstliche status-Datei ohne Paketinhalt. Der Status installed darin ist ausdrücklich erfunden und registriert nichts im Hostsystem.

Quelle, am 2026-11-13 gelesen: [dpkg-Projekt: dpkg-query-Handbuch](https://man7.org/linux/man-pages/man1/dpkg-query.1.html)

## 3. Syntax

```text
dpkg-query [OPTIONEN] {-W|-s|-L|-S} [PAKET_ODER_MUSTER]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--admindir=PFAD` | Administrative Datenquelle für diese Abfrage wählen. |
| `-W`, `--show` | Passende Datensätze mit wählbarem Format. |
| `-f FORMAT` | Feldreferenzen wie ${Version}; Shell vor Expansion schützen. |
| `-s` | Statusdatensatz anzeigen. |
| `-L` | Verwaltete Dateiliste des Pakets. |
| `-S MUSTER` | Dateizugehörigkeit suchen, kein Dateiinhaltsvergleich. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
uebung="$(mktemp -d -t netmon-dpkg-query-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
mkdir db
cat > db/status <<'EOF'
Package: lernpaket
Status: install ok installed
Priority: optional
Section: misc
Installed-Size: 0
Maintainer: Lernteam <lernen@example.invalid>
Architecture: all
Version: 1.2-1
Description: Rein erfundener Statusdatensatz

EOF
dpkg-query --version
LC_ALL=C dpkg-query --admindir="$uebung/db" -W -f='${Package}	${Version}	${Status}
' lernpaket
```

### Schritt 3: Ergebnis einordnen

Erwartet werden lernpaket, 1.2-1 und install ok installed. Einfache Anführungszeichen erhalten die Feldplatzhalter für dpkg-query. Ausschließlich die selbst erzeugte Datenbank wird gelesen. Es wurde kein echtes Paket installiert und kein realer Bestand inventarisiert. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

**Abfragesyntax lernen:** Status und Version aus eigenen Daten ausgeben. **Inventarberichte planen:** Datenbankzustand nicht mit Anwendungsfunktion verwechseln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Berichte können sensible Softwarebestände offenlegen. Nicht einfach --admindir weglassen, wenn nur Testdaten gemeint sind. Ein vorhandener Datenbankpfad sagt nichts über Integrität aller Paketdateien aus. Keine Hostdatenbank oder Paketdatei wurde geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| No packages found | Muster oder gewählte Datenquelle prüfen. |
| Platzhalter leer | Shell hat expandiert; Format einfach zitieren. |
| installed in Testdatei | Nur künstlicher Datensatz, kein Installationsbeweis. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** dpkg-query 1.22.6. Praktisch geprüft: Eigene künstliche status-Datei mit --admindir abgefragt und drei Felder geprüft. Keine Abfrage oder Änderung am Hostbestand. Dateilisten, Integrität, Multiarch und andere Versionen praktisch offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `dpkg` | Schreibende Paketverwaltung und Versionslogik. |
| `apt-cache` | Repositorymetadaten statt Installationsstatus. |
| `dpkg-deb` | Metadaten einer Archivdatei. |

Ausgangsdatensatz 458 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
