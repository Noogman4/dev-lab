---
id: "unzstd"
name: "unzstd"
command: "unzstd"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive & kompression", "unzstd"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 19
reviewed_at: "2026-11-13"
locally_checked_version: "Zstandard CLI 1.5.5"
---

# unzstd – Zstandard-Dateien dekomprimieren und prüfen

## 1. Kurzbeschreibung

`unzstd` ist die Dekompressionsvariante des Zstandard-Kommandozeilenwerkzeugs. Der Aufruf entspricht `zstd -d`. Er stellt den Inhalt komprimierter Dateien wieder her.

**Für eigene Dateien sind keine Root-Rechte nötig.** Zstandard behält die Eingabe standardmäßig auch nach erfolgreicher Dateiausgabe. Dieser Unterschied zu `gunzip` und `unxz` ist wichtig. Trotzdem handelt es sich beim Entpacken um eine Schreiboperation.

## 2. Was macht der Befehl?

Ein Zstandard-Datenstrom wird in seine ursprünglichen Bytes zurückverwandelt. Aus `notiz.txt.zst` kann `notiz.txt` entstehen. Mit `-o` wird das Ziel ausdrücklich gewählt. Ein `.tar.zst` wird dabei zunächst nur zu einem TAR-Datenstrom; die Archivmitglieder werden dadurch noch nicht einzeln angelegt.

Der Aufrufname legt den Modus fest. Unterstützung weiterer Eingabeformate hängt vom Build ab. Nicht jede Datei mit einer ähnlichen Endung ist deshalb kompatibel. Wenn bei der Erstellung ein Wörterbuch verwendet wurde, kann genau dieses auch zur Dekompression nötig sein.

Quellen: [offizielle Zstandard-CLI-Referenz 1.5.7](https://raw.githubusercontent.com/facebook/zstd/v1.5.7/programs/zstd.1.md) sowie die lokal geprüfte Hilfe der Version 1.5.5. Spätere Zusatzoptionen werden hier nicht als lokal getestete Funktionen ausgegeben.

## 3. Syntax

```text
unzstd [OPTIONEN] [EINGABE ...] [-o AUSGABE]
zstd -d [OPTIONEN] [EINGABE ...] [-o AUSGABE]
```

```bash
unzstd -t "probe.zst"
unzstd "probe.zst" -o "probe.txt"
unzstd -c "probe.zst"
```

Der Test schreibt keine normale Ausgabedatei. Die zweite Zeile wählt einen Dateipfad. Die dritte schreibt auf stdout; eine darauf folgende Shell-Umleitung besitzt eigene Überschreibwirkungen.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-d`, `--decompress` | Dekomprimieren. | Durch `unzstd` bereits gewählt. |
| `-t`, `--test` | Verarbeiten und Ausgabe verwerfen. | Vorhandene Prüfwerte werden geprüft; keine Absenderprüfung. |
| `-o DATEI` | Ausgabe ausdrücklich benennen. | Für einen freien, übersichtlichen Zielpfad. |
| `-c`, `--stdout` | Auf stdout ausgeben. | Behält die Quelle und legt selbst keine namensabhängige Ausgabe an. |
| `-k`, `--keep` | Quelle erhalten. | Bereits Standard, kann die Absicht dokumentieren. |
| `--rm` | Quelle nach erfolgreicher Verarbeitung entfernen. | Ändert den Standard und ist für die Übung unnötig. |
| `-D DATEI` | Wörterbuch verwenden. | Muss zur Eingabe passen und erhalten bleiben. |
| `-M128MB` | Dekompressionsspeicher begrenzen. | Beispiel eines Limits; keine Grenze für die Ausgabedateigröße. |
| `-l` | Informationen über Zstandard-Dateien anzeigen. | Metadatenansicht statt vollständiger Wiederherstellung. |
| `-f`, `--force` | Schutzprüfungen übergehen. | Ermöglicht unter anderem Überschreiben; kann bei stdout Fremddaten durchreichen. |
| `-v`, `--verbose` | Mehr Angaben ausgeben. | Meldungen und Abschlussstatus gemeinsam beachten. |
| `--` | Optionen beenden. | Bei führendem Bindestrich im Dateinamen hilfreich. |

Das Überschreibverhalten nicht allein aus einem interaktiven Versuch ableiten: Bei vorhandenen Zielen kann eine Nachfrage oder eine Ablehnung erfolgen. `-f` vermeidet die Nachfrage durch Erzwingen, nicht durch zusätzliche Sicherheit.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Version und Übungsordner

```bash
unzstd --version
uebung="$(mktemp -d -t netmon-unzstd-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Wechsel fortfahren. Keine privaten Dokumente als Testquelle verwenden.

### Schritt 2: Bekannte kleine Datei komprimieren

```bash
printf '%s\n' 'Eigene Zstandard-Testnotiz.' > "original.txt"
zstd "original.txt" -o "probe.zst"
```

Der Packer erzeugt die spätere Testeingabe. `original.txt` bleibt standardmäßig erhalten. Bei einer erneuten Übung einen neuen Arbeitsordner wählen, statt bestehende Dateien zu erzwingen.

### Schritt 3: Komprimierte Eingabe prüfen

```bash
unzstd -t "probe.zst"
```

Dieser Lauf verwirft die dekomprimierten Bytes. Fehlermeldungen zuerst klären. Die Existenz einer komprimierten Datei allein beweist keine vollständige Verarbeitung.

### Schritt 4: Ausgabe bewusst benennen

```bash
unzstd "probe.zst" -o "probe.txt"
cmp "original.txt" "probe.txt"
```

Bei den bekannten Testdaten sollte `cmp` ohne Ausgabe erfolgreich enden. Die komprimierte Eingabe bleibt vorhanden. Ein bereits belegtes `probe.txt` wird nicht ungeprüft ersetzt.

### Schritt 5: Bekannten Text lesen

```bash
unzstd -c "probe.zst"
```

Die eigene Textzeile erscheint auf stdout. Für binäre oder unbekannte Inhalte stattdessen eine kontrollierte Datei beziehungsweise ein passendes Folgewerkzeug wählen.

## 6. Typische Anwendungsfälle

**Eigene komprimierte Daten wiederherstellen:** Eine freie Ausgabedatei ausdrücklich auswählen und bekannte Inhalte nach dem Entpacken vergleichen.

**Komprimierte Archive vorbereiten:** Erst Zstandard-Schicht entfernen, dann die enthaltene TAR-Struktur separat behandeln. Dafür reicht eine Dekompression allein nicht.

**Test vor einer Verarbeitung:** `-t` kann bestimmte Datenfehler erkennen, bevor Ausgaben angelegt werden. Für wichtige Fremddaten weiterhin Herkunft und vollständigen Übertragungsweg prüfen.

**Wörterbuchbasierte Bestände lesen:** Das verwendete Wörterbuch gehört zu den Voraussetzungen einer späteren Wiederherstellung. Es muss zusammen mit dem Verfahren dokumentiert und verfügbar gehalten werden.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Vorhandene Ziele und Originalerhalt

Der Standard erhält die komprimierte Quelle. Mit `--rm` kann dies ausdrücklich geändert werden. Ein vorhandenes Ziel und eine Shell-Umleitung können dennoch Datenverlust verursachen. Eingabe und Ausgabe nie identisch wählen; `-f` nicht reflexartig ergänzen.

### Ressourcen und Prüfwerte

Eine kleine komprimierte Datei kann eine große Ausgabe erzeugen. Ein Speicherlimit betrifft den Decoder, keine Plattenplatzquote. Zstandard-Dateien können Inhaltsprüfwerte besitzen; ein erfolgreicher Vergleich beweist keine sichere Herkunft oder harmlosen Inhalt. `--no-check` nicht zur vermeintlichen Reparatur verwenden.

### Wörterbücher und Dateimetadaten

Ein fehlendes beziehungsweise falsches Wörterbuch kann die Dekompression verhindern. Ein Zstandard-Datenstrom ersetzt außerdem kein vollständiges Dateisystemarchiv mit Eigentümern, ACLs und Verzeichnisstruktur. Für solche Anforderungen den darüberliegenden Archiv- und Sicherungsablauf planen.

### Erzwingen kann die Aussage verändern

Mit `-f` und stdout können unbekannte Daten unverändert durchgereicht werden. Eine Ausgabe ist dann kein Beweis dafür, dass eine gültige Zstandard-Datei dekomprimiert wurde. Für Formatprüfung den normalen Testmodus ohne diese Aufweichung verwenden.

**Root-Rechte sind für die eigenen Beispielpfade nicht erforderlich.** Sie beheben weder ein falsches Wörterbuch noch beschädigte Daten.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Ziel existiert bereits | Früherer Lauf hat eine Ausgabe hinterlassen. | Freien Ausgabepfad wählen. |
| Wörterbuch fehlt | Eingabe wurde mit einer zusätzlichen Voraussetzung erstellt. | Passendes Originalwörterbuch beschaffen und prüfen. |
| Speicherbedarf zu groß | Benötigtes Fenster überschreitet das gewählte Limit. | Herkunft und Bedarf beurteilen, Limit bewusst anpassen. |
| Format nicht unterstützt | Falscher Inhalt oder Build ohne betreffende Methode. | Format und lokale Hilfe prüfen. |
| Ergebnis bleibt `.tar` | Nur Kompressionsschicht entfernt. | Archiv separat auflisten und entpacken. |
| Ausgabe trotz fremder Daten | Force-/Pass-through-Verhalten aktiv. | Ohne Erzwingen testen; tatsächliches Format klären. |

Ein nicht erfolgreicher Abschluss erfordert die genaue Meldung. Nicht lediglich auf eine entstandene Datei vertrauen.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Version prüfen und eigenen Arbeitsordner verwenden.
2. Ausgabepfad mit `-o` ausdrücklich wählen.
3. Quelle zunächst erhalten; `--rm` vermeiden.
4. Vor einer wichtigen Wiederherstellung testen.
5. RAM und Ausgabespeicher getrennt betrachten.
6. Bekannte Inhalte nach dem Entpacken vergleichen.

**Prüfstand:** Zstandard CLI 1.5.5 wurde mit eigenen kleinen Testdaten geprüft: Erstellen der Eingabe, `unzstd -t`, Dateiausgabe mit `-o` und stdout waren erfolgreich; die Inhalte waren bytegleich. Die komprimierte Quelle blieb erhalten. Ein vorhandenes geändertes Testziel wurde ohne interaktive Zustimmung nicht ersetzt. Wörterbücher, große Fenster, Fremdformate und beschädigte Daten wurden nicht praktisch getestet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `zstd` | Hauptprogramm mit Kompression und Dekompression. |
| `zstdcat` | stdout-Variante mit zusätzlichem Force-Verhalten. |
| `tar` | Archiviert eine Dateisammlung vor oder nach der Kompressionsschicht. |
| `unxz`, `gunzip` | Andere Formate und abweichende Regeln zum Originalerhalt. |
| `cmp` | Vergleicht bekannte Original- und Ausgabedateien. |

Ausgangseintrag: Datensatz 19 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
