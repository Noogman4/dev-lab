---
id: "tsk_recover"
name: "tsk_recover"
command: "tsk_recover"
category: "Forensik & Recovery"
language: "de"
root_required: false
risk_level: "caution"
tags: ["tsk_recover", "forensik & recovery"]
status: "Offizielle Sleuth-Kit-Manpage geprüft; kein Export gestartet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 341
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# tsk_recover – Dateien aus einem Abbild in eine getrennte Ablage exportieren

## 1. Kurzbeschreibung

`tsk_recover` aus The Sleuth Kit exportiert Dateien aus einem Abbild in ein lokales Ausgabeverzeichnis. Je nach Auswahl werden nicht zugeordnete, zugeordnete oder alle unterstützten Dateien betrachtet.

**Für ein eigenes lesbares Abbild und einen eigenen beschreibbaren Zielordner sind keine Root-Rechte nötig.** Der Export ist dennoch eine Schreibaktion mit möglicherweise großem Umfang.

## 2. Was macht der Befehl?

Die [offizielle tsk_recover-Manpage](https://www.sleuthkit.org/sleuthkit/man/tsk_recover.html) beschreibt den Standard und die Auswahlvarianten. Standardmäßig werden nicht zugeordnete Dateien versucht. `-a` beschränkt auf zugeordnete Dateien, `-e` umfasst beide Gruppen.

Ein Export setzt verwertbare Dateisysteminformationen voraus. Bei gelöschten Einträgen können Inhalte fehlen oder verändert sein. Ein angelegter Ergebnisname beweist deshalb keine vollständige Wiederherstellung der ursprünglichen Daten.

Die Auswahl unterscheidet sich von einem gewöhnlichen Kopieren eines gemounteten Ordners. Sie kann auch Bereiche betreffen, die im normalen aktuellen Dateibaum nicht sichtbar sind. Das erhöht die Bedeutung eines klaren Untersuchungsumfangs.

## 3. Syntax

```text
tsk_recover [OPTIONEN] ABBILD AUSGABEVERZEICHNIS
tsk_recover -a partition.img NEUE_AUSGABE
tsk_recover -e partition.img NEUE_AUSGABE
```

Abbild und Ausgabeverzeichnis sind verschiedene Argumente. Der Zielordner darf weder die Eingabe ersetzen noch auf das betroffene Originaldateisystem führen.

## 4. Wichtige Optionen

| Option | Aufgabe | Geltungsbereich |
| --- | --- | --- |
| Ohne `-a`/`-e` | Nicht zugeordnete Dateien versuchen. | Nicht automatisch sämtliche aktuellen Dateien. |
| `-a` | Nur zugeordnete Dateien exportieren. | Engere Auswahl. |
| `-e` | Zugeordnete und nicht zugeordnete Dateien exportieren. | Kann erheblich mehr Ausgabe erzeugen. |
| `-o SEKTOREN` | Bestimmtes Volume auswählen. | Ohne Auswahl kann die Suche mehrere Volumes umfassen. |
| `-d KENNUNG` | Bestimmten Verzeichniseintrag auswählen. | Braucht eindeutigen Dateisystemkontext. |
| `-f TYP` | Dateisystemtyp bestimmen. | Nicht mit Abbildformat verwechseln. |
| `-i TYP` | Abbildformat bestimmen. | Muss zur Eingabe passen. |
| `-b BYTES` | Gerätesektorgröße angeben. | Grundlage der Positionsangaben. |
| `-v` | Ausführliche Meldungen zeigen. | Sensible Pfade können sichtbar werden. |
| `-V` | Version anzeigen. | Kein Datenexport. |

Für `-d` verlangt das Handbuch eine konkret ausgewählte Partition über `-o`, sofern ein Volume-System vorhanden ist. Eine Kennung ohne diese Zuordnung wäre mehrdeutig.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen begrenzten Export planen

Angenommen, `./analyse/partition.img` ist eine eigene bekannte Partitionskopie. Gesucht ist zunächst nur ein Export der zugeordneten Dateien, nicht eine breite Suche nach sämtlichen Resten.

### Schritt 2: Auswahl und Ziel benennen

```text
tsk_recover -a ./analyse/partition.img ./export-lauf-01
```

Der Zielname bezeichnet eine neue eigene Ablage. Der Aufruf wurde nicht ausgeführt: Werkzeug und geeignetes Übungsabbild sind lokal nicht vorhanden. Es wird kein tatsächlich geretteter Datenbestand behauptet.

### Schritt 3: Den Standard nicht falsch annehmen

Ohne `-a` wäre der Auftrag nach Handbuch ein anderer. Der bloße Wegfall eines Schalters bedeutet hier nicht „gleicher Export mit Standarddetails“, sondern eine andere Dateiauswahl.

### Schritt 4: Ergebnisse mit dem Auftrag vergleichen

Nach einem späteren Lauf Fehler, Umfang und erwartete Inhalte kontrollieren. Teilergebnisse trotz Fehlern sind möglich. Aus der Existenz des Ordners allein keine vollständige erfolgreiche Rettung ableiten.

## 6. Typische Anwendungsfälle

- Einen bewusst ausgewählten Dateibestand aus einer Kopie exportieren.
- Aktuelle und nicht zugeordnete Inhalte unter getrennten Aufträgen betrachten.
- Eine bekannte Dateisystemanalyse um neue Ergebnisdateien ergänzen.
- Einen eingegrenzten Verzeichnisbereich bei eindeutigem Kontext exportieren.

Für eine einzelne bekannte Datei kann `icat` überschaubarer sein. Ein vollständigerer Export ist sinnvoll, wenn die zusätzliche Datenmenge tatsächlich benötigt und vorgesehen ist.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der Export kann sehr viel Speicherplatz beanspruchen. Auf einem geteilten Ziel kann dadurch auch anderer Betrieb beeinträchtigt werden. Platz, Schutz und getrennte Laufordner vorher planen.

Nicht zugeordnete Bereiche können alte vertrauliche Inhalte enthalten. Einen breiten Export nicht ohne passenden Auftrag ausführen. Wiedergewonnene aktive Dateien nicht ungeprüft starten.

Das Originalmedium bleibt als Ausgabeziel ungeeignet. Neue Schreibzugriffe könnten noch benötigte Datenreste überschreiben. Auch eine unveränderte Eingabekopie sollte zur späteren Nachvollziehbarkeit erhalten bleiben.

## 8. Häufige Fehler

- **Ohne Optionen alle Dateien erwartet:** Der dokumentierte Standard ist enger und anders ausgerichtet.
- **`-a` als „all“ lesen:** Hier bedeutet es zugeordnete Dateien.
- **Kennung ohne Volume-Kontext:** `-d` braucht eine eindeutige Zuordnung.
- **Vorhandener Ordner als Erfolg:** Inhalt und Fehlerstatus fehlen.
- **Ziel auf Quelle:** Kann Rettungsmöglichkeiten zerstören.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer bekannten Arbeitskopie und ausdrücklich begrenzter Auswahl beginnen. Jeden Lauf separat ablegen und den vollständigen Aufruf notieren.

Gefundene Dateien zunächst als Ergebnisse mit unbekannter Qualität behandeln. Bei wichtigen Daten bekannte Referenzen oder Sicherungen zum Abgleich verwenden; eine passend wirkende Endung reicht nicht.

## 10. Verwandte Befehle

- `fls`: Einträge und Kennungen vor einem Export betrachten.
- `icat`: Einen gezielt ausgewählten Inhalt ausgeben.
- `fsstat`: Dateisystemkontext lesen.
- `mmls`: Volume-Lage bestimmen.
- `photorec`: Anderer, inhaltsbasierter Rettungsansatz.

**Prüfstand:** Herstellerhandbuch gelesen. Kein Export, kein Gerätezugriff, keine Mountaktion und keine tatsächliche Wiederherstellung durchgeführt.

Ausgangsdatensatz 341 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
