---
id: "icat"
name: "icat"
command: "icat"
category: "Forensik & Recovery"
language: "de"
root_required: false
risk_level: "caution"
tags: ["icat", "forensik & recovery"]
status: "Sleuth-Kit-Manpage geprüft; keine Datei extrahiert"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 334
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# icat – ausgewählte Dateiinhalte aus einem Abbild ausgeben

## 1. Kurzbeschreibung

`icat` aus The Sleuth Kit gibt Dateiinhalte anhand einer Metadatenkennung aus einem Dateisystemabbild aus. Der Inhalt landet standardmäßig auf der Standardausgabe. Es ist kein gewöhnliches Öffnen eines Dateinamens des laufenden Systems.

**Für eine eigene lesbare Abbilddatei sind keine Root-Rechte nötig.** Ein Mount ist nicht erforderlich. Das Speichern einer Ausgabe braucht einen eigenen, geeigneten Zielpfad.

## 2. Was macht der Befehl?

Die [offizielle icat-Manpage](https://www.sleuthkit.org/sleuthkit/man/icat.html) beschreibt die Inhaltsausgabe. Eine Kennung kann zuvor mit `fls` bestimmt werden. Abbild, Dateisystembeginn und Kennung müssen dabei aus demselben Untersuchungskontext stammen.

Bei gelöschten Dateien können die gespeicherten Verweise oder Inhalte unvollständig sein. Die Ausgabe kann dann Restdaten oder inzwischen veränderte Bereiche enthalten. Ein vorhandener Dateiname oder eine Kennung garantiert keinen intakten Inhalt.

Für eine Analyse ist außerdem wichtig, ob normale Dateiinhalte oder bewusst zusätzliche Speicherbereiche ausgegeben wurden. Solche Varianten sind nicht automatisch bytegleich mit dem ursprünglichen gewöhnlichen Dateistrom.

## 3. Syntax

```text
icat [OPTIONEN] ABBILD METADATENKENNUNG
icat partition.img 123
icat -o STARTSEKTOR laufwerk.img 123
```

`123` ist hier eine frei gewählte Beispielkennung. `STARTSEKTOR` muss aus der bekannten Lage des Dateisystems stammen. Keine der Formen wurde lokal ausgeführt.

## 4. Wichtige Optionen

| Option | Zweck | Konkrete Grenze |
| --- | --- | --- |
| `-f TYP` | Dateisystemtyp angeben. | Muss zur Eingabe passen. |
| `-i TYP` | Abbildformat angeben. | Andere Ebene als Dateisystemtyp. |
| `-o SEKTOREN` | Dateisystembeginn bestimmen. | Einheit und Sektorgröße beachten. |
| `-b BYTES` | Gerätesektorgröße festlegen. | Nicht beliebig aus der Dateigröße ableiten. |
| `-r` | Techniken für gelöschte Dateien verwenden. | Kein garantierter Wiederherstellungserfolg. |
| `-s` | Slack-Bereich zusätzlich ausgeben. | Ergebnis kann über normalen Dateiinhalt hinausgehen. |
| `-h` | Löcher einer Sparse-Datei auslassen. | Verändert die logische Positionsdarstellung. |
| `-v` | Diagnoseausgabe erweitern. | Standardfehler getrennt behandeln. |
| `-V` | Version zeigen. | Großes V beachten. |

Besonders wichtig: `-h` bedeutet hier nicht Hilfe. Ein aus Gewohnheit eingesetzter Hilfsschalter würde die Bedeutung eines Inhaltsaufrufs verändern.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine bekannte Kennung voraussetzen

Angenommen, eine frühere Auswertung einer eigenen Arbeitskopie habe den benötigten Eintrag bestimmt. In diesem Dokument liegt keine solche echte Auswertung vor; Abbild und Kennung bleiben Beispieldaten.

### Schritt 2: Ausgabe nur in eine neue eigene Datei planen

```text
icat ./analyse/partition.img 123 > ./rettung/neue-datei.bin
```

Die Zielablage muss bereits geeignet vorbereitet und die Datei neu beziehungsweise ausdrücklich freigegeben sein. Eine gewöhnliche Shellumleitung kann eine bestehende Datei schon vor dem Programmstart leeren. Die Zeile wird hier nicht ausgeführt.

### Schritt 3: Daten und Fehler nicht vermischen

Die Standardausgabe enthält die Nutzdaten. Standardfehler enthält Meldungen. Beides nicht mit `2>&1` in die gerettete Datei zusammenführen, sonst könnten Textmeldungen deren Inhalt verfälschen.

### Schritt 4: Ergebnis prüfen

Nach einem späteren echten Lauf wären Status, Größe und erwarteter Inhalt zu vergleichen. Eine teilweise geschriebene Datei kann trotz Fehler existieren. Ihre bloße Existenz ist deshalb kein Erfolgskriterium.

## 6. Typische Anwendungsfälle

- Eine bewusst ausgewählte Datei aus einem Abbild extrahieren.
- Einen Eintrag aus einer `fls`-Auflistung inhaltlich betrachten.
- Gelöschte Daten mit bekanntem Kontext zu retten versuchen.
- Zusätzliche Bereiche nur bei einer ausdrücklich entsprechenden Analyse ausgeben.

Für eine normale Wiederherstellungsdatei die Standarddarstellung nicht unnötig durch Slack oder ausgelassene Sparse-Löcher verändern. Jede solche Wahl muss zur Fragestellung passen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Binärdaten im Terminal können die Anzeige stören. Ein unbekannter Inhalt ist nicht automatisch ein lesbares Textdokument. Ausgabeziel bewusst festlegen und mögliche aktive Inhalte nicht starten.

Die größte Schreibgefahr liegt häufig in der Shellumleitung. Sie darf weder auf das Eingabeabbild noch auf wichtige vorhandene Dateien zeigen. Rettungsdaten außerdem nicht zurück auf das betroffene Originalmedium schreiben.

Ausgaben können alte vertrauliche Inhalte enthalten. Ihre Aufbewahrung braucht denselben Schutz wie die untersuchten Daten.

## 8. Häufige Fehler

- **Kennung aus anderem Abbild:** Keine verlässliche Zuordnung.
- **`-h` als Hilfe verwenden:** Bedeutet bei `icat` etwas anderes.
- **Fehlertext in Nutzdaten:** Ausgabeströme wurden vermischt.
- **Datei existiert, also gerettet:** Umfang und Status fehlen.
- **`-s` unbemerkt ergänzt:** Ergebnis enthält mehr als normalen Dateiinhalt.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer bekannten Arbeitskopie und einer einzigen eindeutig zugeordneten Kennung beginnen. Ziel und Quellpfad vor einer Umleitung in Worten vergleichen.

Eine extrahierte Datei zunächst als ungeprüftes Analyseergebnis behandeln. Bei wichtigen Daten bekannte Größen oder verlässliche Referenzhashes hinzunehmen; ein Dateisuffix genügt nicht.

## 10. Verwandte Befehle

- `fls`: Namen und Kennungen suchen.
- `istat`: Zugehörige Metadaten betrachten.
- `fsstat`: Dateisystemkontext lesen.
- `mmls`: Partitionsebene bestimmen.
- `sha256sum`: Extrahierte Inhalte identifizieren.

**Prüfstand:** Herstellerhandbuch gelesen. Keine reale Quelle geöffnet, kein Inhalt ausgegeben und keine Zieldatei durch Umleitung erzeugt.

Ausgangsdatensatz 334 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
