---
id: "testdisk"
name: "testdisk"
command: "testdisk"
category: "Forensik & Recovery"
language: "de"
root_required: false
risk_level: "danger"
tags: ["testdisk", "forensik & recovery"]
status: "Herstelleranleitung und Manpage geprüft; keine Analyse- oder Schreibaktion"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 340
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# testdisk – Partitionsanalyse und mögliche Reparaturen trennen

## 1. Kurzbeschreibung

`testdisk` analysiert Datenträgerstrukturen und bietet Funktionen zur Wiederherstellung beziehungsweise Reparatur. Eine lesende Suche und das Schreiben einer neuen Partitionsstruktur sind deutlich verschiedene Aktionen.

**Für eine eigene lesbare Abbilddatei ist Root nicht grundsätzlich nötig.** Für geschützte physische Geräte und entsprechende Änderungen sind zusätzliche Rechte erforderlich. Das Beispiel bleibt bei einer geplanten Arbeitskopie.

## 2. Was macht der Befehl?

Die [Projektübersicht](https://www.cgsecurity.org/wiki/TestDisk), die [Schrittanleitung des Herstellers](https://www.cgsecurity.org/wiki/TestDisk_Step_By_Step) und die [TestDisk-Manpage](https://manpages.debian.org/trixie/testdisk/testdisk.8.en.html) beschreiben Analyse und mögliche Korrekturen.

TestDisk kann nach verlorenen Partitionen suchen und je nach Dateisystem weitere Funktionen anbieten. Das Erkennen einer Struktur ist nicht dasselbe wie die zuverlässige Wiederherstellung jeder gelöschten Datei. Unterstützung für ein Dateisystem bedeutet nicht automatisch Unterstützung jeder Rettungsart darauf.

Gefundene ältere Strukturen können sich mit heutigen Bereichen überschneiden. Deshalb darf nicht jeder Suchtreffer einfach gleichzeitig als neue aktive Partition übernommen werden.

## 3. Syntax

```text
testdisk ABBILD
testdisk /log ABBILD
testdisk /version
```

Die Oberfläche ist interaktiv. Der Start allein beschreibt noch nicht, welche Menüpunkte anschließend gewählt werden. Die mit Schrägstrich beginnenden Optionen nicht ungeprüft durch übliche GNU-Formen ersetzen.

## 4. Wichtige Optionen

| Form oder Menü | Zweck | Einordnung |
| --- | --- | --- |
| `/version` | Version anzeigen. | Keine Geräteprüfung. |
| `/log` | Protokoll schreiben. | Zusätzliche Ausgabe. |
| `/debug` | Diagnoseinformationen erweitern. | Mehr möglicherweise sensible Details. |
| `/list` | Partitionsübersicht anfordern. | Den tatsächlichen Zielkontext vorher klären. |
| `Analyse` | Aktuelle Struktur betrachten und Suche vorbereiten. | Noch keine fachliche Freigabe zum Schreiben. |
| `Quick Search` | Erste Suche durchführen. | Ergebnis bleibt zu bewerten. |
| `Deeper Search` | Weitergehende Suche durchführen. | Kann lange dauern und viele Kandidaten liefern. |
| `Write` | Bestätigte Struktur schreiben. | Verändert Quelle beziehungsweise Arbeitskopie. |

Konkrete Menüangebote hängen von der Quelle und Version ab. Ein universeller Reparaturknopf wird hier nicht vorausgesetzt.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine bekannte Kopie auswählen

Angenommen, `./analyse/laufwerk-arbeitskopie.img` ist eine eigene Kopie und das Original bleibt unangetastet. Für eine Untersuchung muss ihre Herkunft und Art bekannt sein. Hier wurde kein solches Abbild bereitgestellt oder geöffnet.

### Schritt 2: Einen geplanten Start beschreiben

```text
testdisk /log ./analyse/laufwerk-arbeitskopie.img
```

Der Aufruf würde die interaktive Analyse öffnen und eine Protokollierung anfordern. Er wurde nicht ausgeführt, weil `testdisk` lokal fehlt. Ein tatsächlich erzeugtes Log oder Suchergebnis wird nicht behauptet.

### Schritt 3: Suchergebnis vor Schreiben bewerten

Ein fiktiver Treffer müsste mit erwarteter Größe, Lage und lesbaren Strukturen zusammenpassen. Eine bekannte Dateiliste kann helfen, genügt aber nicht für jede strukturelle Entscheidung. Überlappende Kandidaten benötigen besonders sorgfältige Zuordnung.

### Schritt 4: An der Änderungsgrenze stoppen

`Write`, Bootsektorkopien oder ähnliche Reparaturen verändern Daten. Sie gehören nicht in diese reine Dokumentationsübung. Ein solcher späterer Auftrag braucht einen begründeten Plan und eine erhaltene unveränderte Ausgangskopie.

## 6. Typische Anwendungsfälle

- Eine vermutete verlorene Partition auf einer Arbeitskopie untersuchen.
- Einen möglichen Strukturfehler genauer beschreiben.
- Eine dateisystemspezifische Kopierfunktion nutzen, sofern sie zum konkreten Fall passt.
- Eine Reparatur erst nach nachvollziehbarer Analyse vorbereiten.

Für reine Inhaltsrettung ohne ursprüngliche Dateisystemstruktur kann PhotoRec einen anderen Ansatz bieten. Das ist kein Beweis, dass ein bestimmter Verlustfall damit erfolgreich gelöst wird.

## 7. Risiken, Nebenwirkungen und Vorsicht

Eine falsche Partitions- oder Bootsektoränderung kann bisher zugängliche Daten unerreichbar machen. Schreibfunktionen nicht bestätigen, nur weil ein Suchtreffer plausibel aussieht.

Ein automatisch erkanntes Partitionierungsschema ist eine Hypothese des Werkzeugs und muss zur Quelle passen. Ein Partitionsabbild darf nicht gedankenlos wie ein vollständiges Laufwerk behandelt werden.

Wiederhergestellte Dateien und Logs können vertrauliche Inhalte enthalten. Zielablage und freier Platz sind vor einem Export zu planen. Nichts auf das betroffene Originaldateisystem zurückschreiben.

## 8. Häufige Fehler

- **Jeden Treffer übernehmen:** Alte und aktuelle Strukturen können überlappen.
- **Analyse gleich Reparatur:** Bis zur Schreibbestätigung sind das getrennte Schritte.
- **Unterstütztes Dateisystem gleich jede Undelete-Funktion:** Funktionsgrenzen beachten.
- **Bootfähigkeit als einziges Ziel:** Datenbestand und tatsächliche Struktur bleiben wichtig.
- **Unbekannte Quelle formatieren:** Kann vorhandene Rettungschancen verschlechtern.

## 9. Sichere Varianten oder Tipps für Einsteiger

Vorhandene Backups und eine unveränderte Aufnahme zuerst berücksichtigen. Auf einer eigenen Kopie lernen, welche Menüs nur lesen und welche schreiben. Im Zweifel vor einer Reparaturentscheidung stoppen.

Bei physisch fehlerhaften Medien ist die Aufnahme selbst ein eigener Rettungsschritt. Eine lange Suche auf dem Original ist nicht automatisch die passende erste Maßnahme.

## 10. Verwandte Befehle

- `photorec`: Inhaltsbasierte Dateirettung.
- `mmls`: Lesende Bereichsübersicht aus Abbildern.
- `fsstat`, `fls`: Dateisystemstruktur und Namen betrachten.
- `ddrescue`: Aufnahme bei Lesefehlern unter eigenem Plan.
- `guymager`: Grafische Datenträgeraufnahme.

**Prüfstand:** Herstellerquellen und Manpage gelesen. Kein Start, keine Suche, kein Log, kein Mount und keine Reparatur durchgeführt.

Ausgangsdatensatz 340 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
