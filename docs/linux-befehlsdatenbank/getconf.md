---
id: "getconf"
name: "getconf"
command: "getconf"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "getconf"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 593
reviewed_at: "2026-11-13"
locally_checked_version: "glibc 2.39-0ubuntu8.9"
---

# getconf – Konfigurationsgrenzen eines eigenen Pfads abfragen

## 1. Kurzbeschreibung

getconf fragt benannte System- oder Pfadkonfigurationswerte ab.

## 2. Was macht der Befehl?

Systemwerte beruhen etwa auf sysconf oder confstr; Pfadwerte auf pathconf. Für einen Pfadwert muss ein passender Pfad angegeben werden. NAME_MAX betrifft die Länge eines einzelnen Dateinamens im betrachteten Dateisystem, nicht die Gesamtlänge aller Pfadkomponenten. Ein ausgegebener Wert ist keine Aufforderung, diese Grenze auszureizen.

Quelle, am 2026-11-13 gelesen: [libc-bin: getconf-Handbuch](https://manpages.debian.org/bookworm/libc-bin/getconf.1.en.html); lokale glibc-Hilfe gelesen

## 3. Syntax

```text
getconf [OPTIONEN] SYSTEM_VARIABLE
getconf [OPTIONEN] PFAD_VARIABLE PFAD
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -v SPEZIFIKATION | Gewünschte Kompilierungsumgebung angeben. |
| -a | Viele Konfigurationswerte anzeigen; keine gezielte Einzelabfrage. |
| NAME_MAX PFAD | Grenze für einzelne Namen am Pfad. |
| LONG_BIT | Anderer, systembezogener Konfigurationswert; nicht hier getestet. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
lesson_limit=$(getconf NAME_MAX .)
printf 'NAME_MAX am eigenen Ordner=%s
' "$lesson_limit"
case "$lesson_limit" in
  ''|*[!0-9]*) exit 1 ;;
esac
test "$lesson_limit" -gt 0
```

### Schritt 3: Ergebnis einordnen

Der Wert wird ausschließlich für den neu angelegten eigenen Ordner abgefragt. Geprüft wird eine positive numerische Antwort; kein Dateiname an einer Systemgrenze wird erzeugt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Grenzwerte für eigene Dateiverarbeitung verstehen; Pfad- und Systemparameter unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Unbestimmte oder nicht unterstützte Werte sind möglich und müssen im Skript behandelt werden. Keine globale Konfiguration wird verändert. Andere Pfade können andere Werte liefern.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Unrecognized variable | Namen und verfügbare Implementierung prüfen. |
| Pfadargument fehlt | Pfadkonfigurationsvariable benötigt einen Pfad. |
| undefined | Keinen numerischen Grenzwert erfinden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** glibc 2.39-0ubuntu8.9. Praktisch geprüft: NAME_MAX am eigenen Ordner geprüft; andere Pfade, Spezifikationen und unbestimmte Werte offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| arch | Andere Architekturangabe. |
| pathconf | Zugrunde liegende API. |
| ulimit | Andere Art von Prozesslimit. |

Ausgangsdatensatz 593 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
