---
id: "scalpel"
name: "scalpel"
command: "scalpel"
category: "Forensik & Recovery"
language: "de"
root_required: false
risk_level: "caution"
tags: ["scalpel", "forensik & recovery"]
status: "Paket-Manpage geprüft; keine Suche oder Extraktion ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 338
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# scalpel – File Carving mit einer geprüften Suchkonfiguration planen

## 1. Kurzbeschreibung

`scalpel` extrahiert mögliche Dateien anhand konfigurierter Anfangs- und Endmerkmale. Der Ansatz heißt File Carving. Er hilft unter Umständen auch ohne intakte Dateinamenstruktur, garantiert aber keine vollständige Wiederherstellung.

**Für eine eigene lesbare Abbilddatei sind keine Root-Rechte nötig.** Ergebnisse und Protokolle benötigen eine eigene beschreibbare Ablage. Direkter Gerätezugriff ist kein Bestandteil dieser Übung.

## 2. Was macht der Befehl?

Die [Scalpel-Manpage bei Debian](https://manpages.debian.org/trixie/scalpel/scalpel.1.en.html) beschreibt Eingabe, Konfiguration und Ausgabe. Suchregeln legen fest, welche Merkmale als mögliche Dateien behandelt werden. Diese Regeln beeinflussen die Treffer wesentlich.

Ein extrahierter Bereich erhält nicht automatisch seine frühere Identität zurück. Name, Ordner und vollständiger Inhalt können verloren sein. Auch zufällig passende oder nur teilweise erhaltene Strukturen sind möglich.

Die Manpage enthält ältere Bezeichnungen und experimentelle Funktionen. Für eine tatsächliche Installation den lokalen Hilfetext und die mitgelieferte Konfiguration heranziehen. Nicht aus jedem Beispiel einen universellen Standard ableiten.

## 3. Syntax

```text
scalpel -h
scalpel -c KONFIGURATION -o AUSGABE ABBILD
scalpel -p -c KONFIGURATION -o AUSGABE ABBILD
```

`ABBILD` ist die Eingabe. Anders als bei `foremost` wählt `-i` hier eine Liste von Eingabepfaden, nicht einfach das einzelne Abbild. Diese Verwechslung kann den gesamten Auftrag verändern.

## 4. Wichtige Optionen

| Option | Zweck | Grenze |
| --- | --- | --- |
| `-h` | Hilfe anzeigen. | Keine Inhaltsanalyse. |
| `-c DATEI` | Suchkonfiguration auswählen. | Unterstützte Muster bewusst aktivieren. |
| `-o VERZEICHNIS` | Ausgabeort wählen. | Muss laut Manpage leer oder noch nicht vorhanden sein. |
| `-p` | Vorschau mit Auditangaben erzeugen. | Keine Nutzdateiextraktion, aber mögliche Protokollausgabe. |
| `-i DATEI` | Liste von Eingaben lesen. | Jede Zeile benennt eine Eingabe. |
| `-s ZAHL` | Bytes am Anfang überspringen. | Verändert den betrachteten Bereich. |
| `-v` | Ausführliche Diagnose zeigen. | Umfang und Vertraulichkeit beachten. |
| `-b` | Unter bestimmten Bedingungen auch ohne gefundenes Ende extrahieren. | Mehr unvollständige Ergebnisse möglich. |

Die dokumentierte Standardvorlage kann auskommentierte Suchregeln enthalten. Ein Lauf mit ungeprüfter Vorlage ist deshalb nicht automatisch eine Suche nach allen gewünschten Typen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Konfiguration getrennt vorbereiten

Angenommen, `./analyse/scalpel-geprueft.conf` ist eine eigene bekannte Konfiguration mit wenigen bewusst ausgewählten Suchregeln. Ihre Erstellung ist ein eigener Schritt; hier werden keine universellen Header erfunden.

### Schritt 2: Vorschau auf einer Kopie planen

```text
scalpel -p -c ./analyse/scalpel-geprueft.conf -o ./vorschau-lauf-01 ./analyse/arbeitskopie.img
```

Das Beispiel ist nicht ausgeführt. `scalpel` ist lokal nicht installiert, und es wurde kein geeignetes Übungsabbild bereitgestellt. Der Vorschauordner ist nur ein geplanter neuer Zielname.

### Schritt 3: Vorschau richtig lesen

Eine Vorschau könnte mögliche Extraktionen beschreiben. Sie bestätigt nicht, dass die entsprechenden Originaldateien vollständig und korrekt vorliegen. Das tatsächliche Prüfen der geretteten Inhalte bleibt eine weitere Aufgabe.

### Schritt 4: Einen echten Lauf gesondert planen

Das Weglassen des Vorschauschalters würde einen anderen Auftrag mit Nutzdateiausgaben ergeben. Dafür Ausgabekapazität und einen neuen passenden Zielordner festlegen. Keine Ergebnisse auf das betroffene Originaldateisystem schreiben.

## 6. Typische Anwendungsfälle

- Einen bewusst eingegrenzten Carving-Auftrag mit eigener Suchkonfiguration vorbereiten.
- Erwarteten Ergebnisumfang zunächst über Vorschauinformationen abschätzen.
- Ein bekanntes Abbild unter nachvollziehbaren Regeln auswerten.
- Einen anderen Rettungsansatz ergänzen, wenn Metadaten nicht genügen.

Wiederholte Läufe getrennt benennen. Sonst bleibt unklar, welches Ergebnis zu welcher Konfiguration oder Eingabekopie gehört.

## 7. Risiken, Nebenwirkungen und Vorsicht

Suchregeln mit großer Reichweite können sehr viele oder übergroße Ergebnisse erzeugen. Das Ziel kann sich füllen. Erlaubte Maximalgrößen und gewählte Merkmale gehören deshalb zur fachlichen Planung.

Vorschau ist nicht vollständig schreibfrei, wenn ein Auditprotokoll entsteht. Diese zusätzliche Ausgabe darf keine wichtigen Dateien oder das Eingabeabbild überschreiben.

Extrahierte Inhalte können vertraulich, beschädigt oder aktiv sein. Dateityp und Endung sind keine Unbedenklichkeitsbestätigung. Ergebnisse nicht automatisch öffnen oder an fremde Dienste übertragen.

## 8. Häufige Fehler

- **Keine Treffer wegen auskommentierter Muster:** Konfiguration prüfen.
- **`-i` wie bei Foremost verwenden:** Hier wird eine Eingabeliste erwartet.
- **Vorschau als abgeschlossene Rettung:** Keine Nutzdateien wurden extrahiert.
- **Nichtleerer Ausgabeordner:** Neuen eigenen Laufordner verwenden.
- **Treffer gleich Originaldatei:** Abgrenzung und Vollständigkeit bleiben zu prüfen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer bekannten Kopie, wenigen Suchregeln und einer getrennten Ausgabe beginnen. Konfiguration und Aufruf gemeinsam mit dem Ergebnis aufbewahren.

Keine unverstandenen experimentellen Optionen einschalten, nur um mehr Treffer zu erhalten. Mehr Ausgabe kann die Qualität der eigentlichen Rettung auch verschlechtern.

## 10. Verwandte Befehle

- `foremost`: Carving mit anderer Oberfläche und Optionsbedeutung.
- `photorec`: Interaktive inhaltsbasierte Rettung.
- `fls`, `icat`: Metadatenbasierte Analyse und gezielte Inhaltsausgabe.
- `hashdeep`: Ergebnisbestände unter klarer Referenz vergleichen.

**Prüfstand:** Manpage gelesen. Keine Eingabe ausgewertet, kein Vorschauprotokoll und keine Rettungsdatei erzeugt.

Ausgangsdatensatz 338 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
