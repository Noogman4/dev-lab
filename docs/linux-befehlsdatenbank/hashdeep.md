---
id: "hashdeep"
name: "hashdeep"
command: "hashdeep"
category: "Forensik & Recovery"
language: "de"
root_required: false
risk_level: "caution"
tags: ["hashdeep", "forensik & recovery"]
status: "Paket-Manpage geprüft; keine Bestandsprüfung ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 333
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# hashdeep – Dateihashes und Referenzbestände vergleichen

## 1. Kurzbeschreibung

`hashdeep` berechnet Dateihashes und kann einen Bestand mit gespeicherten Referenzwerten vergleichen. Ein Audit kann außerdem fehlende oder neue Eingaben sichtbar machen. **Für eigene lesbare Dateien sind keine Root-Rechte nötig.**

Ein Hash ist ein Inhaltsmerkmal, keine automatische Herkunfts- oder Unbedenklichkeitsbestätigung. Der Referenzbestand muss selbst vertrauenswürdig und zum geprüften Umfang passend sein.

## 2. Was macht der Befehl?

Die [hashdeep-Manpage](https://manpages.debian.org/trixie/hashdeep/hashdeep.1.en.html) unterscheidet Berechnung, Treffervergleich und Audit. Diese Aufgaben sind verschieden: Ein bekannter Inhalt kann gefunden werden, während eine vollständige Bestandsprüfung weitere Anforderungen hat.

Für einen aussagekräftigen Vergleich müssen Algorithmus, Eingabemenge und Pfadkontext bekannt sein. Eine nachträglich aus dem fraglichen Zustand neu erzeugte Referenz beantwortet nicht mehr zuverlässig die Frage nach einer vorherigen Veränderung.

Auch der Zeitpunkt ist wichtig. Ändert eine Anwendung Dateien während des Lesens, beschreibt die Liste möglicherweise keinen einheitlichen ruhenden Gesamtzustand. Für umfangreiche Vergleiche braucht es deshalb eine bewusste Aufnahmeplanung.

## 3. Syntax

```text
hashdeep -h
hashdeep -c sha256 DATEI
hashdeep -r -c sha256 VERZEICHNIS
hashdeep -a -k REFERENZDATEI DATEIEN
```

Für Vergleichsmodi wird die passende Referenz mit `-k` geladen. Eine Referenz im hashdeep-Format nicht mit jeder beliebigen selbst geschriebenen Hashliste gleichsetzen.

## 4. Wichtige Optionen

| Option | Zweck | Wichtig für den Umfang |
| --- | --- | --- |
| `-c sha256` | SHA-256 ausdrücklich wählen. | Vermeidet unklaren Algorithmusumfang. |
| `-r` | Unterverzeichnisse einbeziehen. | Kann viele Daten lesen. |
| `-k DATEI` | Bekannte Hashliste laden. | Herkunft und Format prüfen. |
| `-a` | Bestandsaudit wählen. | Referenz und Eingabemenge müssen passen. |
| `-m` | Bekannte Inhalte finden. | Nicht identisch mit vollständigem Audit. |
| `-x` | Unbekannte Inhalte ausgeben. | Kein automatischer Schadsoftwarebefund. |
| `-l` | Relative Pfade ausgeben. | Arbeitsverzeichnis und Aufruf beibehalten. |
| `-v` | Mehr Auditdetails anzeigen. | Bei Bedarf gezielt erweitern. |
| `-h` | Hilfe anzeigen. | Kein Dateibestand gelesen. |

Die dokumentierte Standardberechnung umfasst MD5 und SHA-256. Für einen neuen einfachen Vergleich SHA-256 ausdrücklich zu wählen hält die Fragestellung klar.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen eigenen Übungsbestand anlegen

```bash
(
  umask 077
  uebung="$(mktemp -d -t netmon-hashdeep-XXXXXX)" || exit 1
  mkdir "$uebung/daten" || exit 1
  printf 'Eigene Hashuebung\n' > "$uebung/daten/notiz.txt" || exit 1
  cd "$uebung" || exit 1
  hashdeep -r -l -c sha256 ./daten > referenz.hashdeep || exit 1
  hashdeep -a -v -r -l -c sha256 -k referenz.hashdeep ./daten
)
```

Die Referenz liegt außerhalb des untersuchten Unterordners. Dadurch wird sie nicht während ihrer eigenen Entstehung wieder als Eingabe einbezogen. Das Beispiel wurde nicht ausgeführt; `hashdeep` ist lokal nicht installiert.

### Schritt 2: Pfadkontext konstant halten

Beide Berechnungen finden im gleichen Übungsordner statt und nennen denselben Datenpfad. Eine andere Pfaddarstellung könnte sonst eine Bestandsabweichung suggerieren, obwohl Inhalte gleich sind.

### Schritt 3: Ausgabe nicht auf einen Status verkürzen

Die Manpage weist darauf hin, dass Status `0` trotz bestimmter Lese- oder Berechtigungsfehler möglich ist. Für eine belastbare Aussage müssen deshalb Fehlermeldungen und tatsächlich erfasste Eingaben zusätzlich betrachtet werden.

### Schritt 4: Den Beweisumfang benennen

Ein bestandener Vergleich würde nur den dokumentierten Übungsbestand gegenüber dieser Referenz betreffen. Er wäre keine umfassende Prüfung des Rechners und kein Nachweis, dass der ursprüngliche Inhalt ungefährlich war.

## 6. Typische Anwendungsfälle

- Einen bekannten Dateibestand für spätere Vergleiche dokumentieren.
- Kopierte Daten mit einer verlässlichen Referenz abgleichen.
- Neue, fehlende oder anders zugeordnete Eingaben gezielt untersuchen.
- Identische Inhalte in verschiedenen Ablagen erkennen.

Bei einem echten Release gehört außerdem eine authentisierte Referenz dazu. Eine vom selben unbekannten Ort geladene Hashliste bestätigt ihre eigene Herkunft nicht.

## 7. Risiken, Nebenwirkungen und Vorsicht

Rekursive Läufe können viel Datenträgerlast erzeugen. Referenz- und Berichtsdateien können private Pfadnamen enthalten. Einen vollständigen Homebestand nicht ungefragt als harmlose Übung einlesen.

Hashübereinstimmung bedeutet nicht, dass Inhalt vertrauenswürdig ist. Eine manipulierte Referenz kann einen manipulierten Bestand passend erscheinen lassen. Die Referenz daher nicht zur Beseitigung ungeklärter Abweichungen einfach neu erzeugen.

## 8. Häufige Fehler

- **Referenz im Quellordner erzeugen:** Kann den erfassten Umfang verfälschen.
- **Status `0` als Vollständigkeitsbeweis:** Fehlerausgabe und Eingabemenge fehlen.
- **Andere relative Pfade:** Vergleichskontext hat sich geändert.
- **Unbekannt gleich bösartig:** Bedeutet zunächst nur nicht in dieser Referenz.
- **Neue Referenz als Reparatur:** Ursprüngliche Vergleichsbasis geht verloren.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einem kleinen eigenen Bestand und einem Algorithmus beginnen. Referenz, Ergebnis und eigentliche Daten getrennt halten. Den vollständigen Aufruf und den Arbeitsordner notieren.

Für einzelne Dateien ist `sha256sum` oft leichter zu überblicken. Ein umfangreicheres Audit lohnt sich erst, wenn die zusätzlichen Aussagen zum Bestand tatsächlich benötigt werden.

## 10. Verwandte Befehle

- `sha256sum`: Einzelne SHA-256-Werte und einfache Prüfdateien.
- `md5deep`: Ähnliche Werkzeugfamilie mit anderem Standardalgorithmus und Optionsbedeutungen.
- `cmp`: Zwei konkrete Dateien direkt vergleichen.
- `gpg`, `minisign`: Eine Referenz unter passendem Vertrauenskonzept authentisieren.

**Prüfstand:** Manpage gelesen. Keine Benutzerbestände gehasht, keine Referenz überschrieben und kein erfolgreicher Lauf behauptet.

Ausgangsdatensatz 333 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
