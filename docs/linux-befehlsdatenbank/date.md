---
id: "date"
name: "date"
command: "date"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "caution"
tags: ["date", "grundlagen & hilfe"]
status: "Nur Ausgabeumrechnung ausgeführt; keine Systemzeit geändert"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 351
reviewed_at: "2026-11-13"
locally_checked_version: "GNU-coreutils-Manpage 9.4; festes UTC-Beispiel geprüft"
---

# date – Zeitangaben anzeigen, formatieren und bewusst umrechnen

## 1. Kurzbeschreibung

`date` zeigt Datum und Uhrzeit oder formatiert ausdrücklich angegebene Zeitwerte. Es besitzt außerdem Funktionen zum Stellen der Systemzeit. **Für Anzeigen und Umrechnen sind keine Root-Rechte nötig; Zeitänderungen benötigen besondere Rechte.**

## 2. Was macht der Befehl?

Grundlage ist die lokale GNU-coreutils-Manpage. Ohne besondere Eingabe wird die aktuelle Zeit dargestellt. Mit `--date` lässt sich dagegen ein vorgegebener Wert lesen und ausgeben, ohne ihn als Systemzeit zu setzen.

Zeitzone und Darstellungsformat beeinflussen die Ausgabe. Dieselbe reale Zeit kann an verschiedenen Orten ein anderes Datum haben. Für Protokollvergleiche den Zeitbezug deshalb ausdrücklich angeben.

## 3. Syntax

```bash
date '+%Y-%m-%d %H:%M:%S %z'
date -u -d '2026-11-13 12:34:56 UTC' '+%Y-%m-%dT%H:%M:%SZ'
```

Das führende `+` kennzeichnet das Ausgabeformat. Ohne diese Kennzeichnung darf eine Zeichenfolge nicht ungeprüft als reine Formatangabe behandelt werden.

## 4. Wichtige Optionen

| Form | Zweck | Grenze |
| --- | --- | --- |
| `-d TEXT` | Vorgegebene Zeit darstellen. | Stellt die Uhr nicht. |
| `-u` | UTC verwenden. | Bei einer Setzaktion ebenfalls relevant. |
| `-Iseconds` | ISO-nahe Ausgabe mit Sekunden. | GNU-Form; lokale Unterstützung beachten. |
| `-r DATEI` | Änderungszeit einer Datei anzeigen. | Nicht ihr gesichertes Erstellungsdatum. |
| `-s TEXT` | Systemzeit setzen. | Echte Änderung, hier nicht verwenden. |
| `%Y`, `%m`, `%d` | Jahr, Monat, Tag. | Groß-/Kleinschreibung beachten. |
| `%H`, `%M`, `%S` | Stunde, Minute, Sekunde. | `%m` und `%M` sind verschieden. |
| `%z`, `%s` | Zonenoffset beziehungsweise Epochensekunden. | Unterschiedliche Größen. |

## 5. Beispiel erklärt Schritt für Schritt

Der zweite Syntaxaufruf wurde lokal ausgeführt. Er liest einen festen UTC-Wert und formatiert ihn ebenfalls in UTC. Ergebnis mit Status `0`:

```text
2026-11-13T12:34:56Z
```

`Z` ist im Format ein ausdrücklich gesetztes UTC-Kennzeichen. Das ist hier korrekt, weil `-u` die Ausgabe tatsächlich auf UTC festlegt. Dasselbe Zeichen nicht an eine beliebige Ortszeit hängen.

Dieser Test betraf nur einen festen Wert. Die reale Systemuhr wurde weder gestellt noch hinsichtlich ihrer Genauigkeit geprüft.

## 6. Typische Anwendungsfälle

- Einheitliche Zeitangaben für eigene Berichte erzeugen.
- Einen bekannten Zeitwert in eine andere Darstellung bringen.
- Dateizeitstempel mit klarem Bezug anzeigen.
- Protokollzeiten unter bekannter Zeitzone vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Zeitänderungen können Anmeldung, Zertifikate, Zeitpläne und Protokollreihenfolge beeinflussen. `-s` deshalb nicht zur reinen Formatübung verwenden.

Freie Datumstexte können mehrdeutig sein. Bei wichtigen Vergleichen vollständiges Datum, Jahr und Zeitzone angeben. Sommerzeitübergänge können lokale Zeiten doppelt oder gar nicht auftreten lassen.

## 8. Häufige Fehler

- **`%m` für Minuten:** Dafür ist `%M` vorgesehen.
- **`-d` und `-s` verwechseln:** Anzeige und Uhränderung unterscheiden.
- **UTC-Suffix an Ortszeit:** Falscher Zeitbezug.
- **Dateizeit als Entstehungsbeweis:** Änderungszeit ist keine sichere Herkunftsaussage.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einem festen Beispielwert und einer ausdrücklich benannten Zone üben. Keine administrativen Rechte für die Formatierung verwenden.

Bei Skripten ein eindeutig festgelegtes Format verwenden. Lokalisierte Monatsnamen nicht ungeprüft als maschinenunabhängige Schnittstelle behandeln.

## 10. Verwandte Befehle

- `cal`, `ncal`: Kalenderansicht.
- `stat`: Dateizeitstempel und andere Metadaten.
- `timedatectl`: Zeitverwaltung mit lesenden und verändernden Funktionen.
- `printf`: Formatierte Ausgabe mit anderer Syntax.

**Prüfstand:** Feste UTC-Umrechnung erfolgreich geprüft. Keine Systemzeit- oder Zeitzonenänderung.

Ausgangsdatensatz 351 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
