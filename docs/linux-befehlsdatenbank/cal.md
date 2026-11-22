---
id: "cal"
name: "cal"
command: "cal"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["cal", "grundlagen & hilfe"]
status: "Debian-Handbuch der ncal-Variante geprüft; kein Kalenderlauf"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 346
reviewed_at: "2026-11-13"
locally_checked_version: "cal lokal nicht installiert"
---

# cal – einen Monats- oder Jahreskalender anzeigen

## 1. Kurzbeschreibung

`cal` zeigt einen Kalender im Terminal. Es verwaltet keine Termine und stellt keine Uhr um. **Root-Rechte sind nicht nötig.** Ohne Datum wird gewöhnlich der aktuelle Monat angezeigt.

## 2. Was macht der Befehl?

Die hier zugrunde gelegte [Debian-Manpage aus dem Paket ncal](https://manpages.debian.org/trixie/ncal/cal.1.en.html) beschreibt die traditionelle Monatsansicht. Andere Implementierungen können andere Optionen anbieten.

Das Programm berechnet eine Darstellung für Monat und Jahr. Für reproduzierbare Dokumentation diese Werte ausdrücklich angeben, statt eine vom Aufrufzeitpunkt abhängige Ansicht vorauszusetzen.

Ein Kalenderfeld ist keine Feiertagsdatenbank und kein rechtlich verbindlicher Fristenrechner. Historische Kalenderwechsel können zudem von Ort und Implementierung abhängen.

## 3. Syntax

```bash
cal 11 2026
cal 2026
```

Zwei Zahlen bedeuten hier Monat und Jahr; eine einzelne Zahl bezeichnet das Jahr. `cal 26` ist deshalb keine Abkürzung für 2026. Jahreszahlen vollständig ausschreiben.

## 4. Wichtige Optionen

| Form | Zweck | Grenze |
| --- | --- | --- |
| `cal MONAT JAHR` | Bestimmten Monat zeigen. | Implementierung beachten. |
| `cal JAHR` | Jahresansicht anfordern. | Kann breite Ausgabe erzeugen. |
| `-3` | Nachbarmonate einbeziehen. | Nicht mit jeder anderen Auswahl sinnvoll kombinierbar. |
| `-h` | Heutige Hervorhebung abschalten. | In dieser Variante keine Hilfeoption. |
| `-j` | Tage innerhalb des Jahres nummerieren. | Kein Wechsel zum historischen julianischen Kalender. |

Für eine Montag-zuerst-Ansicht bietet die dokumentierte ncal-Variante andere Möglichkeiten. `cal -m` nicht blind aus Anleitungen anderer Implementierungen übernehmen.

## 5. Beispiel erklärt Schritt für Schritt

```bash
cal 11 2026
```

`11` wählt November, `2026` das vollständige Jahr. Die Ausgabe würde die Wochentagsanordnung dieses Monats darstellen. Der Aufruf wurde lokal nicht ausgeführt, weil `cal` nicht installiert ist; eine konkrete Kalenderzeile wird nicht als gemessen angegeben.

Zuerst die Kopfzeile der Wochentage lesen. Je nach Darstellung beginnt die Woche anders als in einem gewohnten Papierkalender. Dann die betreffende Tageszahl in der passenden Spalte suchen.

## 6. Typische Anwendungsfälle

- Eine Monatsübersicht neben einer eigenen Planung anzeigen.
- Den Wochentag eines Datums nachschlagen.
- Eine ausdrücklich datierte Beispielansicht vorbereiten.
- Monatsgrenzen beim Lesen von Protokollzeiträumen überblicken.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der normale Aufruf ist eine Anzeige. Irrtümer entstehen vor allem durch falsche Jahreszahlen, andere Wochenanfänge oder die Verwechslung mit Feiertags- und Fristenregeln.

Bei historischen Daten den zugrunde gelegten Kalenderwechsel prüfen. Für verbindliche Fristen reichen Kalenderdarstellung und eigenes Abzählen allein nicht aus.

## 8. Häufige Fehler

- **Zweistelliges Jahr:** Kann ein anderes Jahrhundert beziehungsweise tatsächliches kleines Jahr meinen.
- **`-h` für Hilfe halten:** Hier wird Hervorhebung abgeschaltet.
- **Optionen einer anderen Variante:** Lokales Handbuch prüfen.
- **Feiertage erwartet:** Keine allgemeine Feiertagsberechnung.

## 9. Sichere Varianten oder Tipps für Einsteiger

Monat und vierstellige Jahreszahl ausdrücklich angeben. Für konkrete Formatoptionen zuerst feststellen, welche Implementierung installiert ist.

Eine fehlende Installation ist kein Anlass, die Systemuhr zu verändern. Die Anzeige und die Zeitverwaltung sind verschiedene Aufgaben.

## 10. Verwandte Befehle

- `ncal`: Alternative Kalenderdarstellung.
- `date`: Daten formatieren und Zeitangaben auswerten.
- `man`: Implementierungsbezogene Bedienung lesen.

**Prüfstand:** Distributionshandbuch gelesen; keine Installation und keine Kalenderausgabe lokal ausgeführt.

Ausgangsdatensatz 346 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
