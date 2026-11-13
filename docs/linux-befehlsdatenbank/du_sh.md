---
id: "du_sh"
name: "du -sh"
command: "du -sh"
category: "Aufgabenorientierte Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["aufgabenorientierte hilfe", "du_sh"]
status: "Ausgearbeitet; Größenabfragen an eigenen Testdateien geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 54
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils du 9.4"
---

# du -sh – Speicherverbrauch eines ausgewählten Bestands zusammenfassen

## 1. Kurzbeschreibung

`du -sh` summiert den von einem ausgewählten Bestand gemeldeten Speicherverbrauch und zeigt pro Argument eine gut lesbare Gesamtsumme. `-s` bedeutet Zusammenfassung und `-h` lesbare Größeneinheiten.

**Für eigene zugängliche Dateien sind keine Root-Rechte nötig.** Der normale Aufruf löscht oder konvertiert keine Dateien. Der rekursive Zugriff kann bei großen Beständen trotzdem Zeit und I/O verursachen.

## 2. Was macht der Befehl?

Du läuft durch erreichbare Dateien beziehungsweise Verzeichnisse und ermittelt deren Verbrauch anhand der Dateisystemangaben. Der Standard ist nicht einfach die Summe sichtbarer logischer Dateilängen. Eine kleine Datei kann einen ganzen Block belegen; eine Sparse-Datei kann große logische Länge mit weniger belegten Blöcken besitzen.

Für mehrere Argumente entstehen mehrere Summen. Hardlinks werden standardmäßig nicht unbeschränkt mehrfach wie unabhängige Kopien gezählt. Snapshots, gemeinsam genutzte Blöcke, Kompression und besondere Dateisystemregeln können weitere Einordnung erfordern.

Grundlagen: [Distributions-Manpage zu du](https://manpages.debian.org/trixie/coreutils/du.1.en.html) und lokale Hilfe von GNU coreutils 9.4. Eine Bestandsgröße ist nicht dasselbe wie verfügbarer Platz im Dateisystem.

## 3. Syntax

```text
du -sh [OPTIONEN] PFAD ...
```

```bash
du -sh -- "Material"
du -sh -- "Ordner eins" "Ordner zwei"
```

`--` beendet die Optionen; danach bleiben Namen mit führendem Bindestrich Datenargumente. Anführungszeichen schützen Leerzeichen und verhindern unbeabsichtigte Shell-Erweiterungen.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-s`, `--summarize` | Nur Gesamtsumme je Argument. | Unterordner werden weiterhin für die Summe untersucht. |
| `-h`, `--human-readable` | Gerundete Einheiten auf Basis 1024. | Keine exakte Byteangabe. |
| `--si` | Basis 1000 verwenden. | Anderer Zahlenwert trotz gleichem Bestand. |
| `-b`, `--bytes` | Apparente Größe in Bytes. | Entspricht nicht automatisch belegten Blöcken. |
| `--apparent-size` | Logische Größen statt normalem Verbrauch. | Sparse-Dateien besonders beachten. |
| `-B1` | Ausgabe des normalen Verbrauchs in Byteeinheiten. | Andere Messgröße als `-b`. |
| `-d N`, `--max-depth=N` | Berichtstiefe begrenzen. | Nicht allgemeine Grenze, wie weit zur Summierung gelesen wird. |
| `-x`, `--one-file-system` | Andere Dateisysteme beim Durchlauf auslassen. | Kann eingehängte Unterbestände bewusst ausschließen. |
| `-L` | Symbolischen Links folgen. | Kann den tatsächlichen Umfang erweitern. |
| `-P` | Links nicht dereferenzieren. | GNU-Standard der hier beschriebenen Variante. |
| `-l`, `--count-links` | Hardlinks mehrfach zählen. | Verändert die Bedeutung der Summe. |
| `--exclude=MUSTER` | Passende Einträge auslassen. | Muster zitieren; Summe beschreibt dann nur die Auswahl. |
| `--inodes` | Inode-Verbrauch untersuchen. | Andere Größe als Byteverbrauch. |
| `-0` | Ausgaben mit NUL trennen. | Für bewusst robuste eigene Verarbeitung hilfreich. |

Ein Bericht mit `-d 1` kann zur Einordnung direkter Unterordner nützen. Er ist kein Ersatz für die klare Definition, welche Mounts, Links und Rechtebereiche in die Messung gehören.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Testdaten anlegen

```bash
du --version
uebung="$(mktemp -d -t netmon-du-XXXXXX)"
cd "$uebung"
pwd
mkdir "Material"
printf '%s\n' 'Eigene Größenprobe.' > "Material/notiz.txt"
```

Nur nach erfolgreichem Wechsel fortfahren. Keine große Benutzerablage als ersten Test vollständig scannen.

### Schritt 2: Zusammenfassung lesen

```bash
du -sh -- "Material"
```

Die Zahl enthält den zusammengefassten gemeldeten Verbrauch des ausgewählten Ordners. Sie kann größer sein als die wenigen Textbytes der Notiz.

### Schritt 3: Apparente Bytes vergleichen

```bash
du -sb -- "Material"
```

Diese Variante beschreibt apparente Größen. Auch Verzeichniseinträge tragen je nach Dateisystem zur angezeigten Summe bei. Nicht erwarten, dass der Wert exakt nur der Nutztextlänge entspricht.

### Schritt 4: Normalen Verbrauch in Bytes ansehen

```bash
du -s -B1 -- "Material"
```

Die Einheit ist nun ein Byte, die Messgröße bleibt normaler Verbrauch. Das kann trotz gleicher Einheit einen anderen Wert als `-sb` liefern.

### Schritt 5: Ergebnis auf die konkrete Frage beziehen

Für „Wie viel umfasst mein ausgewählter Bestand?“ ist die Auswahl entscheidend. Für „Passt eine neue Datei noch aufs Ziel?“ zusätzlich das richtige Dateisystem mit `df` betrachten. Keine Löschentscheidung automatisch an eine einzelne Summe binden.

## 6. Typische Anwendungsfälle

**Eigene Projektgröße ansehen:** Einen klar begrenzten Pfad wählen und beachten, ob große Build-Artefakte oder eingebundene Unterverzeichnisse dazugehören.

**Große Teilbestände eingrenzen:** Mit bewusst gewählter Berichtstiefe die nächsten Kandidaten lesen, ohne sofort Änderungen durchzuführen.

**Dateigröße und Plattenverbrauch unterscheiden:** Apparente Länge mit normalen Verbrauchsangaben vergleichen, etwa bei Sparse-Dateien oder vielen kleinen Dateien.

**Bericht vorbereiten:** Messmethode, Linkbehandlung und ausgeschlossene Bereiche dokumentieren, damit Zahlen später sinnvoll vergleichbar bleiben.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Unvollständiger Zugriff liefert unvollständigen Bestand

Fehlende Leserechte oder parallel verschwindende Dateien können Meldungen und unvollständige Summen erzeugen. Nicht jede Zahl trotz Fehler ist eine vollständige Messung. Erhöhte Rechte nicht automatisch ergänzen.

### Link- und Mountumfang

`-L` kann weitere Ziele einbeziehen. Ohne passende Grenze können eingehängte Unterverzeichnisse zum Bestand zählen. `-x` kann umgekehrt Daten ausschließen, die fachlich dazugehören. Beide Varianten anhand der konkreten Frage wählen.

### Aufwand und Momentaufnahme

Große Bäume und Netzwerkpfade können langsam sein. Parallel veränderte Daten ergeben keine unveränderliche Inventur. Eine begrenzte Berichtstiefe verringert nicht zwangsläufig die notwendige Traversierung für Gesamtsummen.

### Zahlen verschiedener Werkzeuge

Du und df haben unterschiedliche Messgegenstände. Dateisystemreservierungen, geöffnete gelöschte Dateien oder Snapshots lassen sich nicht allein durch Summieren sichtbarer Dateien erklären. Ein Unterschied ist kein automatischer Beleg für verlorene oder verdächtige Daten.

### Berichte und Weiterverarbeitung

Pfade können private Namen enthalten. Ein umgeleiteter Bericht schreibt eine Datei und kann bestehende Inhalte ersetzen. Für beliebige Dateinamen eine bewusst sichere Trennung statt unzitierter Shell-Schleifen verwenden.

**Root-Rechte sind für eigene zugängliche Testdaten nicht nötig.** Der lesende Auftrag erlaubt keine anschließende automatische Bereinigung.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Summe größer als Dateilängen | Blockbelegung und Verzeichnisverwaltung. | Verbrauch und apparente Größe trennen. |
| Summe kleiner als erwartet | Rechtefehler, Hardlinks, Sparse-Dateien oder Ausschlüsse. | Meldungen und Messmethode prüfen. |
| Dauert lange trotz `-s` | Rekursive Summierung bleibt nötig. | Zielumfang bewusst begrenzen. |
| Df zeigt andere Belegung | Andere Messgegenstände. | Dateisystembesonderheiten gezielt klären. |
| Weitere Datenträger mitgemessen | Unterhalb des Pfads eingehängt. | Gewünschte Mountgrenze prüfen. |
| Namen falsch ausgewählt | Shell-Muster oder Leerzeichen. | Pfade zitieren und Auswahl lesen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit einem eigenen begrenzten Ordner anfangen.
2. `-s` als Ausgabezusammenfassung verstehen, nicht als oberflächliche Messung.
3. Byteeinheit und Art der gemessenen Größe auseinanderhalten.
4. Rechtefehler und Ausschlüsse mitberichten.
5. Für freien Platz zusätzlich df am richtigen Ziel verwenden.
6. Keine Dateien allein wegen einer großen Zahl automatisch löschen.

**Prüfstand:** GNU du 9.4 untersuchte ausschließlich einen eigenen temporären Ordner mit einer 1024-Byte-Testdatei. `-sh`, `-sb` und `-s -B1` endeten erfolgreich; die apparente Summe war mindestens so groß wie die Testdatei. Der Inhalt blieb unverändert. Sparse-Dateien, Hardlinks, Mountgrenzen, Quoten und Netzwerkpfade wurden nicht praktisch getestet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `df` | Platzstatistik des zugehörigen Dateisystems. |
| `stat` | Eigenschaften einzelner Dateien. |
| `find` | Bestände anhand gezielter Merkmale auswählen. |
| `findmnt` | Mountgrenzen und Zuordnungen lesen. |

Ausgangseintrag: Datensatz 54 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
