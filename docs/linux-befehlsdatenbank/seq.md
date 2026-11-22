---
id: "seq"
name: "seq"
command: "seq"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["seq", "grundlagen & hilfe"]
status: "Keine unbegrenzte Ausgabe oder Schleifenaktion gestartet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 367
reviewed_at: "2026-11-13"
locally_checked_version: "GNU-coreutils-Manpage 9.4 gelesen"
---

# seq – begrenzte Zahlenfolgen ausgeben

## 1. Kurzbeschreibung

`seq` erzeugt eine Zahlenfolge zwischen gewählten Grenzen. Die Zahlen werden normalerweise zeilenweise ausgegeben. **Root-Rechte sind nicht nötig.** Die Ausgabe führt keine weiteren Aktionen aus.

## 2. Was macht der Befehl?

Die lokale GNU-Manpage beschreibt Anfang, Schrittweite und Ende. Fehlende Anfangs- und Schrittwerte werden normalerweise mit `1` ergänzt. Eine absteigende Folge benötigt deshalb eine ausdrücklich passende negative Schrittweite.

Zahlenfolgen können später Schleifen speisen. Dann stammen mögliche Datei- oder Systemänderungen von deren Befehlen, nicht allein von der Zahlenanzeige.

## 3. Syntax

```bash
seq 3
seq 2 4
seq 5 -2 1
```

Die letzte Form bedeutet Start `5`, Schritt `-2`, Ende `1`. Zwei Zahlen bedeuten dagegen Start und Ende, nicht Start und Schrittweite.

## 4. Wichtige Optionen

| Option | Zweck | Grenze |
| --- | --- | --- |
| `-s TEXT` | Trennzeichen wählen. | Nicht automatisch eine sichere Dateiliste. |
| `-w` | Einheitliche Breite mit Nullen. | Darstellung, keine andere Zahlenmenge. |
| `-f FORMAT` | Unterstütztes Zahlenformat. | Erwartet geeignete Gleitkommaformatierung. |
| `--help` | Bedienung anzeigen. | Kein großer Ausgabelauf. |

Eine Schrittweite von null ist unzulässig. Dezimalwerte und Rundungsgrenzen brauchen bei exakten Anforderungen besondere Aufmerksamkeit.

## 5. Beispiel erklärt Schritt für Schritt

```bash
seq 5 -2 1
```

Erwartete Zahlen sind `5`, `3` und `1`, jeweils auf einer eigenen Zeile. Es wird nicht über die passend erreichte Grenze hinaus weitergezählt.

Das Beispiel wurde nicht gesondert ausgeführt; es ist aus der lokalen Manpage abgeleitet. Es wurde keine mit der Folge gespeiste Schleife gestartet.

Für Einsteiger zunächst eine kleine Grenze wählen. Eine versehentlich riesige Folge kann auch ohne weitere Aktionen viel Ausgabe und Zeit verursachen.

## 6. Typische Anwendungsfälle

- Kleine nummerierte Beispiele erzeugen.
- Einen fest begrenzten eigenen Schleifenzähler vorbereiten.
- Nummern mit einheitlicher Darstellung ausgeben.
- Schrittweiten anschaulich erklären.

## 7. Risiken, Nebenwirkungen und Vorsicht

Große oder praktisch unendliche Grenzen können Ressourcen verbrauchen. Wird die Ausgabe in eine Datei geschrieben, kann das Zielmedium volllaufen.

Eine Zahlenfolge als Eingabe für Lösch- oder Verwaltungsbefehle kann viele echte Aktionen auslösen. Vorher nur die beabsichtigten Werte ausgeben und den Auftrag begrenzen.

## 8. Häufige Fehler

- **Zwei Zahlen als Start und Schritt:** Tatsächlich Start und Ende.
- **Absteigend ohne negativen Schritt:** Gewünschte Folge entsteht nicht.
- **Nullschritt:** Unzulässige Angabe.
- **Dezimalwerte als exakte Finanzrechnung:** Nicht die geeignete Garantie.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit festen kleinen Ganzzahlen beginnen. Für Bash-Ganzzahlschleifen kann eine arithmetische Schleife klarer sein, wenn keine Textfolge benötigt wird.

Zahlenausgabe und anschließende Aktionen getrennt entwerfen. Eine korrekte Folge bestätigt nicht automatisch die Richtigkeit jedes späteren Schleifenbefehls.

## 10. Verwandte Befehle

- `printf`: Zahlen formatieren.
- `expr`: Kleine Ausdrücke auswerten.
- Bash-Arithmetik: Zähler innerhalb der Shell.
- `awk`: Folgen und Berechnungen mit anderer Oberfläche.

**Prüfstand:** Lokale Manpage gelesen. Keine große Folge, Dateiablage oder Verwaltungsserie erzeugt.

Ausgangsdatensatz 367 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
