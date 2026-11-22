---
id: "fsstat"
name: "fsstat"
command: "fsstat"
category: "Forensik & Recovery"
language: "de"
root_required: false
risk_level: "caution"
tags: ["fsstat", "forensik & recovery"]
status: "Offizielle Sleuth-Kit-Manpage geprüft; kein Abbild gelesen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 331
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# fsstat – Dateisystemdetails eines Abbilds lesen

## 1. Kurzbeschreibung

`fsstat` aus The Sleuth Kit zeigt allgemeine Informationen über ein Dateisystem in einem Abbild. Dazu können Typ, Größenbereiche und dateisystemspezifische Strukturangaben gehören. Es repariert diese Struktur nicht.

**Für eine eigene lesbare Abbilddatei sind keine Root-Rechte nötig.** Ein Mount ist für diesen Zugriff nicht erforderlich. Direkter Gerätezugriff bleibt ein anderer, berechtigungsabhängiger Fall.

## 2. Was macht der Befehl?

Die [offizielle fsstat-Manpage](https://www.sleuthkit.org/sleuthkit/man/fsstat.html) erläutert die Ausgabe als dateisystemabhängig. Verschiedene Dateisysteme besitzen unterschiedliche Verwaltungsstrukturen; deshalb ist nicht jede Ausgabezeile überall vorhanden.

Für eine Analyse ist die Eingabegrenze entscheidend: Ein ganzes Laufwerksabbild kann mehrere Dateisysteme enthalten. `fsstat` muss dann das tatsächlich gemeinte Dateisystem erreichen. Ein einzelnes Partitionsabbild kann dagegen direkt an dessen Anfang beginnen.

Ein plausibler Strukturbericht beantwortet noch nicht, ob alle Dateien vollständig lesbar sind. Er ist eine Grundlage für gezielte weitere Betrachtungen, kein vollständiger Integritäts- oder Sicherheitsnachweis.

## 3. Syntax

```text
fsstat [OPTIONEN] ABBILD
fsstat partition.img
fsstat -o STARTSEKTOR laufwerk.img
```

`STARTSEKTOR` ist eine bekannte Lageangabe, keine frei zu erratende Zahl. Einheit und zugrunde gelegte Sektorgröße müssen zusammenpassen. Die Beispiele wurden nicht ausgeführt.

## 4. Wichtige Optionen

| Option | Bedeutung | Beim Verwenden beachten |
| --- | --- | --- |
| `-f TYP` | Dateisystemtyp vorgeben. | Erzwingt keine sinnvolle Interpretation falscher Daten. |
| `-f list` | Unterstützte Dateisystemtypen auflisten. | Nicht mit einer Untersuchung des Abbilds gleichsetzen. |
| `-i TYP` | Abbildformat vorgeben. | Format und Dateisystem sind verschiedene Ebenen. |
| `-i list` | Verfügbare Abbildformate auflisten. | Lokale Ausstattung kann abweichen. |
| `-o SEKTOREN` | Dateisystembeginn festlegen. | Nicht Bytezahl einsetzen. |
| `-b BYTES` | Gerätesektorgröße angeben. | Kein universelles Synonym für Dateisystemblockgröße. |
| `-t` | Nur den erkannten Dateisystemtyp ausgeben. | Engere Ausgabe als der Vollbericht. |
| `-v` | Debugdetails ergänzen. | Kann deutlich mehr Informationen erzeugen. |
| `-V` | Version anzeigen. | Großes V beachten. |

Typenlisten sind ein guter Weg, lokale Unterstützung festzustellen. Sie ersetzen keine Prüfung, ob die konkrete Quelle vollständig und zum erwarteten Format passend vorliegt.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine bekannte Arbeitskopie voraussetzen

Angenommen, `./analyse/partition.img` ist ein freigegebenes Partitionsabbild. Seine Herkunft und Größe sind dokumentiert. Es wird hier nicht erzeugt oder gemountet.

### Schritt 2: Den Bericht planen

```text
fsstat ./analyse/partition.img
```

Der geplante Aufruf würde allgemeine Dateisystemdaten lesen. Er wurde nicht ausgeführt: Werkzeug und geeignete Übungskopie sind lokal nicht vorhanden.

### Schritt 3: Bereiche mit Einheiten lesen

Ein fiktiver Bericht könnte Grenzen für Metadatenkennungen und Inhaltsblöcke nennen. Diese Grenzen beschreiben die interne Struktur des untersuchten Dateisystems. Sie sind keine Liste sämtlicher Dateinamen und keine direkten Hostdateipfade.

### Schritt 4: Passendes Folgewerkzeug wählen

Für Namen wäre anschließend `fls` zuständig, für ausgewählte Inhalte `icat`. Diese Schritte müssen dieselbe Dateisystemlage verwenden. Eine Kennung aus einem anderen Abbild zu übernehmen wäre keine sinnvolle Fortsetzung.

## 6. Typische Anwendungsfälle

- Dateisystemtyp und Strukturbereiche einer bekannten Kopie einordnen.
- Eine gezielte weitere Sleuth-Kit-Analyse vorbereiten.
- Angaben aus einer dokumentierten Aufnahme mit der erkannten Struktur vergleichen.
- Ein Offsetproblem von einem tatsächlichen Dateisystemproblem unterscheiden.

Ein unerwarteter Typ kann auch an einer falschen Lage oder Eingabeart liegen. Nicht automatisch daraus schließen, die Struktur sei manipuliert oder zerstört.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Quelluntersuchung ist lesend. Eine zusätzliche Umleitung des Berichts schreibt jedoch eine Zieldatei, die nicht mit dem Eingabeabbild identisch sein darf.

Strukturangaben können sensible Namen, Kennungen oder Zeitinformationen enthalten. Vor einer Weitergabe auf den tatsächlich benötigten Ausschnitt begrenzen. Zeitfelder im richtigen Dateisystem- und Zeitzonenkontext lesen.

Keine Reparaturaktion auf dem Original anschließen, nur weil eine Strukturangabe ungewohnt erscheint. Eine solche Änderung kann spätere Rekonstruktionen erschweren.

## 8. Häufige Fehler

- **Ganzes Laufwerk ohne passenden Offset:** Das gewählte Dateisystem wird nicht erreicht.
- **Bytes statt Sektoren:** Positionsrechnung prüfen.
- **Abbildformat mit Dateisystemtyp verwechseln:** Zwei unterschiedliche Parameterbereiche.
- **Gültiger Bericht gleich vollständige Datenrettung:** Dateiinhalte wurden noch nicht geprüft.
- **Unbekanntes Feature:** Lokale Werkzeugunterstützung als Prüfpunkt festhalten.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer bekannten, kopierten Quelle beginnen und den Aufruf vollständig notieren. Vor einer Interpretation zuerst Format, Dateisystembeginn und Größenangaben zuordnen.

Die Quelle unverändert halten und Berichte getrennt speichern. Ein Bericht ist ein Analyseergebnis mit Grenzen, keine Aufforderung zur Änderung seiner Eingabe.

## 10. Verwandte Befehle

- `mmls`: Partitionsebene und Bereiche betrachten.
- `fls`: Namen und Verzeichniseinträge lesen.
- `istat`: Einzelne Metadaten untersuchen.
- `icat`: Ausgewählte Dateiinhalte ausgeben.
- `file`: Allgemeine Dateitypmerkmale, mit anderer Tiefe und Aufgabe.

**Prüfstand:** Herstellerhandbuch gelesen. Kein Abbild geöffnet, kein Medium gemountet und keine Reparatur ausgeführt.

Ausgangsdatensatz 331 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
